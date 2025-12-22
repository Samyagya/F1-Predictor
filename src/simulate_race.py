import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
MODEL_PATH = os.path.join('models', 'f1_baseline_model.pkl')
ENCODER_PATH = os.path.join('models', 'encoder.pkl')
PIT_LOSS_SECONDS = 22.0  # Average time lost in a pit stop (approx)
TOTAL_LAPS = 57          # Standard Bahrain distance (can be changed)

def load_artifacts():
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Model not found!")
        exit()
    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)

def simulate_strategy(driver, circuit, start_compound, pit_lap, end_compound):
    model, encoder = load_artifacts()
    
    print(f"\n--- Simulating {driver} at {circuit} ---")
    print(f"Strategy: Start {start_compound} -> Pit Lap {pit_lap} -> Finish {end_compound}")
    
    cumulative_time = 0
    lap_times = []
    
    # State Variables
    current_compound = start_compound
    current_tyre_age = 0  # Fresh tyres at start
    
    print("Lap  | Cmpd | Age | Fuel | Pred Time | Total Time")
    print("-" * 55)

    for lap in range(1, TOTAL_LAPS + 1):
        # 1. Handle Pit Stop
        is_pit_lap = (lap == pit_lap)
        
        if is_pit_lap:
            # We assume the lap time INCLUDES the pit loss
            # But we switch tyres for the NEXT lap
            pass # We calculate the in-lap normally, then add pit loss
            
        # 2. Prepare Input for Model
        # Calculate Fuel (LINEAR BURN: 110kg -> 0kg)
        fuel_weight = 110 * (1 - (lap / TOTAL_LAPS))
        if fuel_weight < 0: fuel_weight = 0
        
        input_data = pd.DataFrame({
            'Driver': [driver],
            'Circuit': [circuit],
            'Compound': [current_compound],
            'TyreLife': [current_tyre_age],
            'LapNumber': [lap],
            'Rainfall': [0],      # Assume dry race for now
            'FuelWeight': [fuel_weight]
        })
        
        # 3. Predict Lap Time
        # Encode
        encoded_data = encoder.transform(input_data)
        # Predict
        pred_seconds = model.predict(encoded_data)[0]
        
        # 4. Add Pit Stop Penalty if applicable
        if is_pit_lap:
            pred_seconds += PIT_LOSS_SECONDS
            note = " (PIT)"
        else:
            note = ""
            
        cumulative_time += pred_seconds
        lap_times.append(pred_seconds)
        
        # Print progress every 5 laps or on pit lap
        if lap % 5 == 0 or is_pit_lap:
            m = int(pred_seconds // 60)
            s = pred_seconds % 60
            total_m = int(cumulative_time // 60)
            print(f"{lap:3d}  | {current_compound[:3]}  | {current_tyre_age:3d} | {int(fuel_weight):3d}  | {m}:{s:05.2f}{note} | {total_m}m")
        
        # 5. Update Car State for NEXT lap
        if is_pit_lap:
            current_compound = end_compound # Change tyres
            current_tyre_age = 0            # Reset age
        else:
            current_tyre_age += 1           # Tyres get older

    print("-" * 55)
    total_m = int(cumulative_time // 60)
    total_s = cumulative_time % 60
    print(f"🏁 TOTAL RACE TIME: {total_m}m {total_s:.2f}s")
    
    return lap_times, cumulative_time

if __name__ == "__main__":
    # Test Case: Max Verstappen, Bahrain, Soft -> Hard Strategy
    # We ask the user for inputs
    d = input("Driver (e.g., VER): ").strip()
    c = input("Circuit (e.g., Sakhir): ").strip()
    
    print("\n--- Strategy A ---")
    s1 = input("Start Compound (SOFT/MEDIUM/HARD): ").strip().upper()
    p1 = int(input("Pit Lap: "))
    e1 = input("End Compound (SOFT/MEDIUM/HARD): ").strip().upper()
    
    laps_a, time_a = simulate_strategy(d, c, s1, p1, e1)