import pandas as pd
import os

# 1. Load the data
# We use 'low_memory=False' to avoid warnings about mixed types
df = pd.read_csv(os.path.join('data', 'processed', 'f1_training_data_v2.csv'), low_memory=False)

def print_unique_sorted(col_name):
    print(f"\n--- 🔍 VALID {col_name.upper()}S ---")
    # Force everything to string so Python doesn't crash sorting numbers vs text
    # We also drop 'nan' so the list is clean
    unique_vals = df[col_name].dropna().astype(str).unique()
    
    # Sort and print
    print(sorted(unique_vals))

# 2. Print the Menus
print_unique_sorted('Driver')
print_unique_sorted('Circuit')
print_unique_sorted('Compound')