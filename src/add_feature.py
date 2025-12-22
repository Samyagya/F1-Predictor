import pandas as pd
import os

# 1. Load the existing data
input_path = os.path.join('data', 'processed', 'f1_training_data.csv')
output_path = os.path.join('data', 'processed', 'f1_training_data_v2.csv')

print("Loading data...")
df = pd.read_csv(input_path)

# 2. Calculate "Race Progress" and "Fuel Load"
# Logic: We find the max laps for each specific race to know how 'done' the race is.
print("Engineering features...")

# Group by RaceID to find the total laps for that specific race
race_lengths = df.groupby('RaceID')['LapNumber'].max().rename('TotalLaps')
df = df.merge(race_lengths, on='RaceID', how='left')

# F1 cars start with ~110kg of fuel. 
# We assume they finish with near 0kg.
# Formula: CurrentFuel = 110kg * (1 - (CurrentLap / TotalLaps))
df['FuelWeight'] = 110 * (1 - (df['LapNumber'] / df['TotalLaps']))

# 3. Save the new "Smart" dataset
# We drop 'TotalLaps' because the AI doesn't need to know it directly, 
# it just needs the FuelWeight result.
df.drop(columns=['TotalLaps'], inplace=True)

df.to_csv(output_path, index=False)
print(f"SUCCESS! Enhanced data saved to: {output_path}")
print(f"Added 'FuelWeight' column. Sample values:\n{df[['LapNumber', 'FuelWeight']].head()}")