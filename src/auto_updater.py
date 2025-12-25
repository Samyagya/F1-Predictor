import fastf1
import pandas as pd
import joblib
import os
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder

# --- CONFIG ---
DATA_PATH = 'data/race_data.csv'  # Make sure you have your main CSV here
MODEL_PATH = 'models/f1_baseline_model.pkl'
ENCODER_PATH = 'models/encoder.pkl'

def get_last_completed_race():
    """Finds the most recent race that has happened."""
    today = datetime.now()
    schedule = fastf1.get_event_schedule(today.year)
    
    # Filter for past races
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
    if race_name in known_races:
        print(f"✅ Data for {race_name} is already up to date. No action needed.")
        return

    print(f"🚀 New Race Detected: {race_name}. Fetching data...")

    # --- FIX: Create cache folder if it doesn't exist ---
    if not os.path.exists('cache'):
        os.makedirs('cache')
    
    
    # 3. Fetch Data via FastF1
    fastf1.Cache.enable_cache('cache') # Optional: Use a cache folder
    session = fastf1.get_session(last_race.year, last_race['RoundNumber'], 'R')
    session.load()
    
    # --- FEATURE ENGINEERING (Simplified to match your Inputs) ---
    laps = session.laps.pick_quicklaps()
    
    new_data = []
    for index, lap in laps.iterrows():
        # This must match the columns your App uses!
        new_data.append({
            'Driver': lap['Driver'],
            'Circuit': race_name,
            'Compound': lap['Compound'],
            'TyreLife': lap['TyreLife'],
            'LapNumber': lap['LapNumber'],
            'Rainfall': 1 if lap['Rainfall'] else 0,
            # Simple Fuel Calc: Start (110kg) - Burn (approx 1.7kg/lap)
            'FuelWeight': max(0, 110 - (lap['LapNumber'] * 1.7)),
            'LapTime': lap['LapTime'].total_seconds() # Target Variable
        })
        
    df_new = pd.DataFrame(new_data)
    
    # 4. Append & Save
    df_updated = pd.concat([df_main, df_new], ignore_index=True)
    df_updated.to_csv(DATA_PATH, index=False)
    print(f"✅ Added {len(df_new)} laps from {race_name}.")

    # 5. RETRAIN MODEL
    print("🧠 Retraining Model...")
    
    # Encode Categoricals
    le = LabelEncoder()
    # We combine Driver/Circuit/Compound into one encoder or separate ones
    # For simplicity, we assume your 'encoder.pkl' handles the transform
    # But usually, you need to refit the encoder on new data
    for col in ['Driver', 'Circuit', 'Compound']:
        df_updated[col] = df_updated[col].astype(str)
        
    # We use a trick: Fit encoder on ALL data
    # (In production you might use OneHotEncoder, but let's stick to your format)
    # NOTE: This creates a simple Ordinal encoder for the update
    df_encoded = df_updated.copy()
    feature_cols = ['Driver', 'Circuit', 'Compound', 'TyreLife', 'LapNumber', 'Rainfall', 'FuelWeight']
    
    # Re-Fit Encoder
    # Important: We need to save this new encoder so the App understands new Drivers/Circuits
    import sklearn.preprocessing
    enc = sklearn.preprocessing.OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    df_encoded[feature_cols[:3]] = enc.fit_transform(df_updated[feature_cols[:3]])
    
    X = df_encoded[feature_cols]
    y = df_updated['LapTime'].fillna(90) # Handle DNF/NaT simple fill
    
    # Train
    model = GradientBoostingRegressor(n_estimators=100)
    model.fit(X, y)
    
    # 6. Save Artifacts
    joblib.dump(model, MODEL_PATH)
    joblib.dump(enc, ENCODER_PATH)
    print("🎉 Model Retrained and Saved!")

if __name__ == "__main__":
    update_dataset_and_train()