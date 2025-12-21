import pandas as pd
import os
import glob
from tqdm import tqdm  # This gives us a nice progress bar

# --- CONFIGURATION ---
RAW_DIR = os.path.join('data', 'raw')
PROCESSED_DIR = os.path.join('data', 'processed')
OUTPUT_FILE = os.path.join(PROCESSED_DIR, 'f1_training_data.csv')

def process_data():
    all_races_data = []
    
    # Get list of all race folders
    race_folders = glob.glob(os.path.join(RAW_DIR, '*'))
    print(f"Found {len(race_folders)} races to process.")

    # Loop through every race folder
    for folder in tqdm(race_folders, desc="Processing Races"):
        try:
            # 1. Load the 3 raw files
            laps_file = os.path.join(folder, 'laps.csv')
            weather_file = os.path.join(folder, 'weather.csv')
            results_file = os.path.join(folder, 'results.csv')

            # Skip if any file is missing (safety check)
            if not (os.path.exists(laps_file) and os.path.exists(weather_file) and os.path.exists(results_file)):
                continue

            laps = pd.read_csv(laps_file)
            weather = pd.read_csv(weather_file)
            results = pd.read_csv(results_file)

            # --- CLEANING: Filter out non-racing laps ---
            # Keep only Green Flag laps (TrackStatus = 1)
            # Remove Pit In/Out laps (PitInTime/PitOutTime must be empty)
            laps = laps[laps['TrackStatus'] == 1]
            laps = laps[laps['PitInTime'].isna() & laps['PitOutTime'].isna()]
            
            # Remove laps with no time
            laps = laps.dropna(subset=['LapTime'])

            # --- MERGING: Connect Weather to Laps ---
            # We need to convert time strings to Timedeltas to match them
            laps['Time'] = pd.to_timedelta(laps['Time'])
            weather['Time'] = pd.to_timedelta(weather['Time'])
            
            # Sort for merge_asof
            laps = laps.sort_values('Time')
            weather = weather.sort_values('Time')
            
            # The Magic Merge: Find the weather closest to the lap time
            # direction='backward' means "look at the weather just before the lap finished"
            merged = pd.merge_asof(laps, weather, on='Time', direction='backward')

            # --- MERGING: Add End-of-Race Results ---
            # We want to know the driver's final position and grid position
            # We merge on 'Driver' (abbreviation)
            # Rename columns in results to avoid conflict (e.g., 'Time' -> 'TotalRaceTime')
            results = results.rename(columns={'Time': 'TotalRaceTime', 'Position': 'FinalPosition'})
            
            # Keep only useful result columns
            results_cols = ['Abbreviation', 'TeamName', 'FinalPosition', 'GridPosition', 'Status']
            merged = pd.merge(merged, results[results_cols], left_on='Driver', right_on='Abbreviation', how='left')

            # --- FEATURE ENGINEERING (Basic) ---
            # Add Race ID from folder name so we know which track this is
            race_id = os.path.basename(folder)
            merged['RaceID'] = race_id
            merged['Year'] = int(race_id.split('_')[0])
            merged['Round'] = int(race_id.split('_')[1])
            merged['Circuit'] = race_id.split('_', 2)[2]

            # Convert LapTime to Seconds (AI understands floats, not "1:24.500")
            # The string format is usually "0 days 00:01:24.500000"
            merged['LapTime_Seconds'] = merged['LapTime'].apply(lambda x: pd.to_timedelta(x).total_seconds())

            all_races_data.append(merged)

        except Exception as e:
            print(f"Skipping {folder} due to error: {e}")

    # Combine all 70 races into one massive table
    if all_races_data:
        final_df = pd.concat(all_races_data, ignore_index=True)
        
        # Create output folder if not exists
        if not os.path.exists(PROCESSED_DIR):
            os.makedirs(PROCESSED_DIR)
            
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nSUCCESS! Processed {len(final_df)} laps.")
        print(f"Saved to: {OUTPUT_FILE}")
        print("Columns:", list(final_df.columns))
    else:
        print("No data processed!")

if __name__ == "__main__":
    process_data()