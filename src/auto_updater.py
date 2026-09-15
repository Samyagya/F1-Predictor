import fastf1
import pandas as pd
import joblib
import os
import time
from datetime import datetime, timezone, timedelta
from sklearn.ensemble import GradientBoostingRegressor
import sklearn.preprocessing

# --- CIRCUIT NAME MAP ---
# FastF1 EventName strings -> short names used by the app and physics engine
# This ensures the encoder trains on the same names the app uses at inference.
CIRCUIT_NAME_MAP = {
    # Bahrain
    'Bahrain Grand Prix': 'Sakhir',
    'Pre-Season Testing': 'Sakhir',
    # Saudi Arabia
    'Saudi Arabian Grand Prix': 'Jeddah',
    # Australia
    'Australian Grand Prix': 'Albert Park',
    # Japan
    'Japanese Grand Prix': 'Suzuka',
    # China
    'Chinese Grand Prix': 'Shanghai',
    # Miami
    'Miami Grand Prix': 'Miami',
    # Emilia Romagna
    'Emilia Romagna Grand Prix': 'Imola',
    # Monaco
    'Monaco Grand Prix': 'Monaco',
    # Canada
    'Canadian Grand Prix': 'Montreal',
    # Spain — 2026 onwards: Madring (IFEMA Madrid), NOT the old Barcelona Catalunya circuit
    'Spanish Grand Prix': 'Madrid',
    'Barcelona Grand Prix': 'Madrid',  # FastF1 may use this name for 2026
    # Austria
    'Austrian Grand Prix': 'Red Bull Ring',
    # Britain
    'British Grand Prix': 'Silverstone',
    # Hungary
    'Hungarian Grand Prix': 'Hungaroring',
    # Belgium
    'Belgian Grand Prix': 'Spa',
    # Netherlands
    'Dutch Grand Prix': 'Zandvoort',
    # Italy
    'Italian Grand Prix': 'Monza',
    # Azerbaijan
    'Azerbaijan Grand Prix': 'Baku',
    # Singapore
    'Singapore Grand Prix': 'Singapore',
    # United States
    'United States Grand Prix': 'Austin',
    # Mexico
    'Mexico City Grand Prix': 'Mexico City',
    'Mexican Grand Prix': 'Mexico City',
    # Brazil
    'São Paulo Grand Prix': 'Interlagos',
    'Brazilian Grand Prix': 'Interlagos',
    # Las Vegas
    'Las Vegas Grand Prix': 'Las Vegas',
    # Qatar
    'Qatar Grand Prix': 'Lusail',
    # Abu Dhabi
    'Abu Dhabi Grand Prix': 'Yas Marina',
}

# --- CONFIG ---
DATA_PATH = 'data/race_data.csv'
MODEL_PATH = 'models/f1_baseline_model.pkl'
ENCODER_PATH = 'models/encoder.pkl'


def get_last_completed_race():
    """
    Finds the most recent race that is fully over.

    BUG C FIX: Use Session5DateUtc (actual race start in UTC) + 3-hour buffer
    instead of EventDate (midnight on race day). This prevents the updater from
    trying to load data before the race has even finished.
    Uses timezone-aware UTC datetime throughout to avoid naive/aware comparison errors.
    """
    now_utc = datetime.now(timezone.utc)
    schedule = fastf1.get_event_schedule(now_utc.year)

    def race_end_utc(row):
        """Return the estimated UTC time the race ends (start + 3hr buffer)."""
        utc = row['Session5DateUtc']
        if pd.isna(utc):
            return pd.Timestamp('1970-01-01', tz='UTC')
        # Session5DateUtc is timezone-naive in the DataFrame — make it UTC-aware
        if hasattr(utc, 'tzinfo') and utc.tzinfo is None:
            utc = utc.replace(tzinfo=timezone.utc)
        return utc + timedelta(hours=3)

    schedule['_RaceEndUtc'] = schedule.apply(race_end_utc, axis=1)

    # Only include rounds with a valid RoundNumber (exclude pre-season testing)
    past_races = schedule[
        (schedule['_RaceEndUtc'] < now_utc) &
        (schedule['RoundNumber'] > 0)
    ]

    if past_races.empty:
        return None

    last_race = past_races.iloc[-1]
    return last_race


def update_dataset_and_train():
    # 1. Load Existing Data
    if os.path.exists(DATA_PATH):
        df_main = pd.read_csv(DATA_PATH)
        known_races = df_main['Circuit'].unique()
    else:
        print("[WARN] No existing dataset found. Starting fresh.")
        df_main = pd.DataFrame()
        known_races = []

    # 2. Check Last Race
    last_race = get_last_completed_race()
    if last_race is None:
        print("No completed races found for this year yet.")
        return

    race_name = last_race['EventName']
    # Map to short circuit name for duplicate-check consistency
    circuit_short_name = CIRCUIT_NAME_MAP.get(race_name, race_name)
    if circuit_short_name in known_races:
        print(f"[OK] Data for {circuit_short_name} is already up to date. No action needed.")
        return

    print(f"[NEW] New Race Detected: {race_name} -> stored as '{circuit_short_name}'. Fetching data...")

    # Auto-create cache folder if it doesn't exist
    os.makedirs('cache', exist_ok=True)

    # 3. Fetch Data via FastF1 (with retry logic)
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 60

    laps = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[RETRY] Attempt {attempt}/{MAX_RETRIES}: Loading session data...")

            # BUG B FIX: Create a FRESH session object on every attempt.
            # Re-using the same session object across retries does not re-fetch
            # from the API — the failed state is cached in the object itself.
            fastf1.Cache.enable_cache('cache')
            session = fastf1.get_session(last_race.year, last_race['RoundNumber'], 'R')

            # Load only what we need — laps + weather. Telemetry is heavy and unnecessary.
            session.load(laps=True, telemetry=False, weather=True, messages=False)

            # BUG A FIX: session.load() does NOT raise an exception when it silently
            # fails to fetch data — it just logs WARNINGs and leaves session.laps empty.
            # We must explicitly check that laps are populated before proceeding.
            if len(session.laps) == 0:
                raise ValueError(
                    "session.load() completed but laps DataFrame is empty — "
                    "data is not yet available on the F1 timing API. Try again later."
                )

            # BUG D FIX: pick_quicklaps() uses outlier detection and can return empty
            # on brand-new circuits with no prior reference data (e.g. Madrid 2026).
            # Fall back to raw laps filtered to < 3 minutes if that happens.
            laps = session.laps.pick_quicklaps()
            if laps.empty:
                print("[WARN]  pick_quicklaps() returned empty — falling back to raw laps with 3-min filter.")
                laps = session.laps[session.laps['LapTime'] < pd.Timedelta('00:03:00')].copy()

            if laps.empty:
                raise ValueError(
                    "No valid laps after all filters — data may be incomplete or not ready yet."
                )

            print(f"[OK] Session loaded on attempt {attempt}. {len(laps)} laps found.")
            break  # success — exit the retry loop

        except Exception as e:
            print(f"[WARN]  Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"   Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print("[ERROR] All retries exhausted. Aborting.")
                raise  # Re-raise so GitHub Actions marks the run as failed

    # BUG E FIX: Guard against laps being None before any post-loop processing.
    # (Can happen if all retries fail and an exception is NOT re-raised.)
    if laps is None or laps.empty:
        print("[ERROR] No lap data available after all retries. Aborting.")
        return

    # Check if Rainfall exists; if not, assume DRY (False/0)
    if 'Rainfall' not in laps.columns:
        print("[WARN]  'Rainfall' column missing from this session. Assuming Dry conditions.")
        laps = laps.copy()
        laps['Rainfall'] = False

    # Warn if circuit not in map (helps catch new GPs before they break things)
    if circuit_short_name == race_name:
        print(
            f"[WARN]  '{race_name}' not found in CIRCUIT_NAME_MAP. Storing as-is. "
            f"Add it to CIRCUIT_NAME_MAP in auto_updater.py and a pit loss entry in physics.py."
        )

    new_data = []
    for index, lap in laps.iterrows():
        new_data.append({
            'Driver': lap['Driver'],
            'Circuit': circuit_short_name,  # Use short name to match app inference
            'Compound': lap['Compound'],
            'TyreLife': lap['TyreLife'],
            'LapNumber': lap['LapNumber'],
            'Rainfall': 1 if lap['Rainfall'] else 0,
            'FuelWeight': max(0, 110 - (lap['LapNumber'] * 1.7)),
            'LapTime': lap['LapTime'].total_seconds()
        })

    df_new = pd.DataFrame(new_data)

    # 4. Append & Save
    df_updated = pd.concat([df_main, df_new], ignore_index=True)
    df_updated.to_csv(DATA_PATH, index=False)
    print(f"[OK] Added {len(df_new)} laps from {race_name} ({circuit_short_name}).")

    # 5. RETRAIN MODEL
    print("[AI] Retraining Model...")

    for col in ['Driver', 'Circuit', 'Compound']:
        df_updated[col] = df_updated[col].astype(str)

    df_encoded = df_updated.copy()
    feature_cols = ['Driver', 'Circuit', 'Compound', 'TyreLife', 'LapNumber', 'Rainfall', 'FuelWeight']

    enc = sklearn.preprocessing.OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    df_encoded[feature_cols[:3]] = enc.fit_transform(df_updated[feature_cols[:3]])

    X = df_encoded[feature_cols]
    y = df_updated['LapTime'].fillna(90)

    model = GradientBoostingRegressor(n_estimators=100)
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(enc, ENCODER_PATH)
    print("[OK] Model Retrained and Saved!")


if __name__ == "__main__":
    update_dataset_and_train()