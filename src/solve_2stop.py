import pandas as pd
import joblib
import os
import itertools
import warnings

warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
MODEL_PATH = os.path.join('models', 'f1_baseline_model.pkl')
ENCODER_PATH = os.path.join('models', 'encoder.pkl')
PIT_LOSS_SECONDS = 22.0
TOTAL_LAPS = 57
COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD'] # The menu of options

def load_artifacts():
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Model not found!")
        exit()
    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)

def get_stint_time(model, encoder, driver, circuit, compound, start_lap, end_lap):
    """Calculates the time for a SINGLE stint (vectorized for speed)."""
    laps = list(range(start_lap, end_lap + 1))
    if not laps: return 0
    
    data = pd.DataFrame({
        'Driver': driver,
        'Circuit': circuit,
        'Compound': compound,
        'TyreLife': range(len(laps)),
        'LapNumber': laps,
        'Rainfall': 0,
        'FuelWeight': [110 * (1 - (l / TOTAL_LAPS)) for l in laps]
    })
    
    # Clip negative fuel
    data.loc[data['FuelWeight'] < 0, 'FuelWeight'] = 0
    
    encoded_data = encoder.transform(data)
    return model.predict(encoded_data).sum()

def solve_2stop():
    model, encoder = load_artifacts()
    
    print("\n--- 🧠 AI GRANDMASTER STRATEGY SOLVER ---")
    print("I will test EVERY tyre combination to find the win.")
    driver = input("Driver (e.g., VER): ").strip()
    circuit = input("Circuit (e.g., Sakhir): ").strip()
    
    print(f"\nSimulating {driver} at {circuit}...")
    print("Testing all valid compound combinations...")
    print("-" * 60)
    print(f"{'STRATEGY':<30} | {'PITS':<10} | {'TIME':<10}")
    print("-" * 60)
    
    global_results = []
    
    # 1. Generate all Permutations (S-S-M, S-M-H, etc.)
    # We check combinations of 3 stints
    perms = list(itertools.product(COMPOUNDS, repeat=3))
    
    for c1, c2, c3 in perms:
        # F1 RULE: Must use at least 2 different compounds in a race
        # (e.g., Soft-Soft-Soft is illegal)
        if len(set([c1, c2, c3])) < 2:
            continue
            
        strategy_name = f"{c1} -> {c2} -> {c3}"
        
        # 2. Optimize Pit Stops for THIS combination
        # We use a coarser search (step=2) to speed up the massive loop
        best_for_combo = (None, None, 999999)
        
        # Pit 1 Window: Lap 10-25 (Step 3)
        for pit1 in range(10, 26, 3):
            time_s1 = get_stint_time(model, encoder, driver, circuit, c1, 1, pit1)
            
            # Pit 2 Window: Pit1+15 to Lap 50 (Step 3)
            for pit2 in range(pit1 + 15, 51, 3):
                time_s2 = get_stint_time(model, encoder, driver, circuit, c2, pit1 + 1, pit2)
                time_s3 = get_stint_time(model, encoder, driver, circuit, c3, pit2 + 1, TOTAL_LAPS)
                
                total_time = time_s1 + time_s2 + time_s3 + (PIT_LOSS_SECONDS * 2)
                
                if total_time < best_for_combo[2]:
                    best_for_combo = (pit1, pit2, total_time)
        
        # Save the best version of this strategy
        global_results.append({
            'Strategy': strategy_name,
            'Pit1': best_for_combo[0],
            'Pit2': best_for_combo[1],
            'TotalTime': best_for_combo[2]
        })
        
        # Print progress (overwrite line to keep clean)
        print(f"\rChecked {strategy_name}...", end="")

    print("\n" + "-" * 60)
    
    # 3. Sort and Show Top 3
    global_results.sort(key=lambda x: x['TotalTime'])
    
    print("\n🏆 TOP 3 WINNING STRATEGIES 🏆")
    for i, res in enumerate(global_results[:3]):
        m = int(res['TotalTime'] // 60)
        s = res['TotalTime'] % 60
        print(f"{i+1}. {res['Strategy']:<25} | Pit {res['Pit1']}, {res['Pit2']} | {m}m {s:05.2f}s")
        
    print(f"\nCompare to 1-Stop Baseline: ~92m 17s")

if __name__ == "__main__":
    solve_2stop()