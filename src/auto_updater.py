import fastf1
import pandas as pd
import joblib
import os
import time
from datetime import datetime
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
    # Spain
    'Spanish Grand Prix': 'Barcelona',
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
    """Finds the most recent race that has happened."""
    today = datetime.now()
    schedule = fastf1.get_event_schedule(today.year)
    
    past_races = schedule[schedule['EventDate'] < today]
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
        print("⚠️ No existing dataset found. Starting fresh.")
        df_main = pd.DataFrame()
        known_races = []

    # 2. Check Last Race
    last_race = get_last_completed_race()
    if last_race is None:
        print("No races found.")
        return

    race_name = last_race['EventName']
    # Map to short circuit name for duplicate-check consistency
    circuit_short_name = CIRCUIT_NAME_MAP.get(race_name, race_name)
    if circuit_short_name in known_races:
        print(f"✅ Data for {circuit_short_name} is already up to date. No action needed.")
        return

    print(f"🚀 New Race Detected: {race_name}. Fetching data...")
    
    # --- FIX 1: Auto-create cache folder ---
    if not os.path.exists('cache'):
        os.makedirs('cache')
    
    # 3. Fetch Data via FastF1 (with retry logic)
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 60

    laps = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"🔄 Attempt {attempt}/{MAX_RETRIES}: Loading session data...")
            fastf1.Cache.enable_cache('cache')
            session = fastf1.get_session(last_race.year, last_race['RoundNumber'], 'R')
            # Use explicit args — mirrors ingest_data.py; avoids loading heavy/unavailable data
            session.load(laps=True, telemetry=False, weather=True, messages=False)
            laps = session.laps.pick_quicklaps()
            if laps.empty:
                raise ValueError("No laps returned after filtering — data may not be ready yet.")
            print(f"✅ Session loaded successfully on attempt {attempt}.")
            break  # success — exit the retry loop
        except Exception as e:
            print(f"⚠️ Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                print(f"   Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print("❌ All retries exhausted. Aborting.")
                raise  # Re-raise so GitHub Actions marks the run as failed
    
    # Check if Rainfall exists; if not, assume DRY (False/0)
    if 'Rainfall' not in laps.columns:
        print("⚠️ 'Rainfall' data missing. Assuming Dry conditions.")
        laps['Rainfall'] = False
    
    # Map the full event name to a short circuit name that matches the app's naming
    circuit_short_name = CIRCUIT_NAME_MAP.get(race_name, race_name)
    if circuit_short_name == race_name:
        print(f"⚠️ '{race_name}' not found in CIRCUIT_NAME_MAP. Storing as-is. Add it to the map in auto_updater.py.")

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
    print(f"✅ Added {len(df_new)} laps from {race_name}.")

    # 5. RETRAIN MODEL
    print("🧠 Retraining Model...")

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
    print("🎉 Model Retrained and Saved!")

if __name__ == "__main__":
    update_dataset_and_train()