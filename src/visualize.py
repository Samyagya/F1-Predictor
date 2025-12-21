import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# 1. Load the Data
print("Loading data...")
data_path = os.path.join('data', 'processed', 'f1_training_data.csv')

if not os.path.exists(data_path):
    print("ERROR: File not found!")
    exit()

df = pd.read_csv(data_path)
print(f"Loaded {len(df)} laps.")

# 2. Filter for Bahrain 2024 (or latest available)
print("Filtering for Bahrain...")
demo_race = df[df['Circuit'].str.contains('Bahrain')].sort_values('Year', ascending=False)

if demo_race.empty:
    print("No Bahrain data found! Checking first available race...")
    # Fallback: Just pick the first race in the dataset
    latest_year = df['Year'].iloc[0]
    circuit = df['Circuit'].iloc[0]
    race_data = df[(df['Year'] == latest_year) & (df['Circuit'] == circuit)]
    print(f"Visualizing {circuit} {latest_year} instead.")
else:
    latest_year = demo_race['Year'].iloc[0]
    race_data = demo_race[demo_race['Year'] == latest_year]
    print(f"Visualizing Bahrain {latest_year}...")

# 3. Plot: Lap Time vs Tyre Age
plt.figure(figsize=(12, 6))
sns.scatterplot(
    data=race_data, 
    x='TyreLife', 
    y='LapTime_Seconds', 
    hue='Compound', 
    palette={'SOFT': 'red', 'MEDIUM': 'yellow', 'HARD': 'white'},
    alpha=0.6
)

plt.style.use('dark_background')
plt.title(f'Tyre Degradation: {latest_year} (All Drivers)')
plt.xlabel('Tyre Age (Laps)')
plt.ylabel('Lap Time (Seconds)')
plt.grid(True, alpha=0.3)

# 4. Save the graph
output_file = 'check_data.png'
plt.savefig(output_file)
print(f"\nSUCCESS! Graph saved to '{output_file}'. Check your file explorer!")