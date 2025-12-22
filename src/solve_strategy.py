import pandas as pd
import joblib
import os
import warnings

warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
MODEL_PATH = os.path.join('models', 'f1_baseline_model.pkl')
ENCODER_PATH = os.path.join('models', 'encoder.pkl')
PIT_LOSS_SECONDS = 22.0
TOTAL_LAPS = 57

def load_artifacts():
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Model not found!")
        exit()
    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)

def get_race_time(driver, circuit, start_compound, pit_lap, end_compound, model, encoder):
    cumulative_time = 0
    
    # State Variables
    current_compound = start_compound
    current_tyre_age = 0 

    for lap in range(1, TOTAL_LAPS + 1):
        is_pit_lap = (lap == pit_lap)
        
        # Physics: Fuel decreases linearly
        fuel_weight = 110 * (1 - (lap / TOTAL_LAPS))
        if fuel_weight < 0: fuel_weight = 0
        
        # Prepare Input
        input_data = pd.DataFrame({
            'Driver': [driver],
            'Circuit': [circuit],
            'Compound': [current_compound],
            'TyreLife': [current_tyre_age],
            'LapNumber': [lap],
            'Rainfall': [0],
            'FuelWeight': [fuel_weight]
        })
        
        # Predict
        encoded_data = encoder.transform(input_data)
        pred_seconds = model.predict(encoded_data)[0]
        
        # Add Pit Cost
        if is_pit_lap:
            pred_seconds += PIT_LOSS_SECONDS
            
        cumulative_time += pred_seconds
        
        # Update State
        if is_pit_lap:
            current_compound = end_compound
            current_tyre_age = 0
        else:
            current_tyre_age += 1
            
    return cumulative_time

def find_optimal_strategy():
    model, encoder = load_artifacts()
    
    print("\n--- 🧠 AI STRATEGY SOLVER ---")
    driver = input("Driver (e.g., VER): ").strip()
    circuit = input("Circuit (e.g., Sakhir): ").strip()
    start_cmpd = input("Start Compound (SOFT/MEDIUM/HARD): ").strip().upper()
    end_cmpd = input("End Compound (SOFT/MEDIUM/HARD): ").strip().upper()
    
    print(f"\nSimulating {driver} at {circuit}...")
    print(f"Testing Pit Window: Lap 10 to Lap 50")
    print("-" * 40)
    print("Pit Lap | Total Time  | Diff to Best")
    print("-" * 40)
    
    results = []
    
    # Test every possible pit lap from 10 to 50
    for pit_lap in range(10, 51):
        total_time = get_race_time(driver, circuit, start_cmpd, pit_lap, end_cmpd, model, encoder)
        results.append((pit_lap, total_time))
    
    # Sort by fastest time
    results.sort(key=lambda x: x[1])
    best_lap, best_time = results[0]
    
    # Print Top 5 Results
    for pit_lap, total_time in results[:10]: # Show top 10
        diff = total_time - best_time
        m = int(total_time // 60)
        s = total_time % 60
        print(f"Lap {pit_lap:2d}  | {m}m {s:05.2f}s | +{diff:.2f}s")
        
    print("-" * 40)
    print(f"🏆 OPTIMAL STRATEGY: Pit on Lap {best_lap}")
    
if __name__ == "__main__":
    find_optimal_strategy()