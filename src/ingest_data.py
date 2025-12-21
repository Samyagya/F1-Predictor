import fastf1
import pandas as pd
import os
import shutil

# --- CONFIGURATION ---
START_YEAR = 2023
END_YEAR = 2025  # Since we are in Dec 2025, we get full history
CACHE_DIR = 'cache'
RAW_DATA_DIR = os.path.join('data', 'raw')

# 1. Setup Cache (Crucial for speed)
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

def process_season(year):
    """Downloads and saves data for an entire season."""
    print(f"\n=== FETCHING SEASON {year} ===")
    
    # Get the schedule for the year
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as e:
        print(f"Error fetching schedule for {year}: {e}")
        return

    # Loop through every round
    for i, row in schedule.iterrows():
        round_num = row['RoundNumber']
        country = row['Country']
        location = row['Location']
        session_date = row['Session5Date'] # Date of the Race
        
        # Skip if the race hasn't happened yet (future proofing)
        if pd.isnull(session_date) or (session_date.tz_localize(None) > pd.Timestamp.now()):
            continue

        # Create a unique ID for this race (e.g., "2024_01_Bahrain")
        race_id = f"{year}_{str(round_num).zfill(2)}_{location.replace(' ', '_')}"
        save_path = os.path.join(RAW_DATA_DIR, race_id)

        # CHECKPOINT: If folder exists, skip it! (Saves time on restart)
        if os.path.exists(save_path):
            print(f"  [SKIP] Found data for {race_id}")
            continue
            
        print(f"  [DOWNLOADING] Round {round_num}: {location}...")

        try:
            # We download the RACE session ('R')
            # You can also add 'Q' for qualifying if you want later
            session = fastf1.get_session(year, round_num, 'R')
            session.load(weather=True, telemetry=False, messages=False) # Lighter load

            # Create the folder
            os.makedirs(save_path, exist_ok=True)

            # --- EXTRACT & SAVE 3 CORE DATASETS ---

            # 1. LAPS (The Physics)
            # We pick specific columns to keep file size small
            laps = session.laps
            laps_cols = ['Driver', 'LapTime', 'LapNumber', 'Stint', 'PitOutTime', 
                         'PitInTime', 'Sector1Time', 'Sector2Time', 'Sector3Time', 
                         'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST', 'Compound', 
                         'TyreLife', 'FreshTyre', 'Team', 'TrackStatus', 'Time']
            # Only save columns that exist (sometimes Speed is missing)
            avail_cols = [c for c in laps_cols if c in laps.columns]
            laps[avail_cols].to_csv(os.path.join(save_path, 'laps.csv'), index=False)

            # 2. WEATHER (The Variable)
            weather = session.weather_data
            weather.to_csv(os.path.join(save_path, 'weather.csv'), index=False)

            # 3. RESULTS (The Target)
            results = session.results
            # Includes Points, GridPosition, Status (DNF/Finished)
            results_cols = ['Abbreviation', 'DriverNumber', 'TeamName', 'Position', 
                            'GridPosition', 'Status', 'Points', 'Time']
            avail_res_cols = [c for c in results_cols if c in results.columns]
            results[avail_res_cols].to_csv(os.path.join(save_path, 'results.csv'))

        except Exception as e:
            print(f"  [ERROR] Failed {race_id}: {e}")
            # If it failed, delete the folder so we retry cleanly next time
            if os.path.exists(save_path):
                shutil.rmtree(save_path)

if __name__ == "__main__":
    # Ensure raw directory exists
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)

    # Run for our target years
    for y in range(START_YEAR, END_YEAR + 1):
        process_season(y)
        
    print("\n\nData Ingestion Complete! Check the 'data/raw' folder.")