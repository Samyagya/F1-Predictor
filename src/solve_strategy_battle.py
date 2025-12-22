import pandas as pd
import joblib
import os
import itertools
import warnings

# --- FIXED IMPORT BLOCK ---
# This tries both ways of importing so it works from any folder
try:
    from src.physics import get_pit_loss, calculate_tyre_cliff_penalty
except ImportError:
    from physics import get_pit_loss, calculate_tyre_cliff_penalty

warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
MODEL_PATH = os.path.join('models', 'f1_baseline_model.pkl')
ENCODER_PATH = os.path.join('models', 'encoder.pkl')
TOTAL_LAPS = 57
COMPOUNDS = ['SOFT', 'MEDIUM', 'HARD']

def load_artifacts():
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Model not found!")
        exit()
    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)

def get_stint_time(model, encoder, driver, circuit, compound, start_lap, end_lap):
    """
    Calculates the total time for a stint, including PHYSICS PENALTIES (Tyre Cliff).
    """
    laps = list(range(start_lap, end_lap + 1))
    if not laps: return 0
    
    # 1. Base Prediction (The AI Model)
    data = pd.DataFrame({
        'Driver': driver,
        'Circuit': circuit,
        'Compound': compound,
        'TyreLife': range(len(laps)), # 0, 1, 2...
        'LapNumber': laps,
        'Rainfall': 0,
        'FuelWeight': [110 * (1 - (l / TOTAL_LAPS)) for l in laps]
    })
    # Clip negative fuel
    data.loc[data['FuelWeight'] < 0, 'FuelWeight'] = 0
    
    encoded_data = encoder.transform(data)
    base_predictions = model.predict(encoded_data)
    
    # 2. Apply Physics Guardrails (The Tyre Cliff)
    total_stint_time = 0
    
    for i, lap_time in enumerate(base_predictions):
        tyre_age = i # Age starts at 0 for this stint
        
        # Ask Physics: "Is this tyre dead?"
        penalty = calculate_tyre_cliff_penalty(compound, tyre_age)
        
        # Add normal lap time + penalty
        total_stint_time += (lap_time + penalty)
        
    return total_stint_time

def solve_battle():
    model, encoder = load_artifacts()
    
    print("\n--- 🏁 STRATEGY SHOOTOUT (v2: PHYSICS ENABLED) ---")
    driver = input("Driver (e.g., VER): ").strip()
    circuit = input("Circuit (e.g., Sakhir): ").strip()
    
    # GET ACCURATE PIT LOSS FOR THIS TRACK
    pit_loss = get_pit_loss(circuit)
    print(f"   ℹ️  Pit Loss for {circuit}: {pit_loss}s")
    
    print(f"\nAnalyzing optimal strategies for {driver} at {circuit}...")
    
    # --- PART 1: OPTIMIZE 1-STOP ---
    print("\n1️⃣  Solving 1-Stop Strategies...")
    best_1stop = {'Time': 999999, 'Desc': ''}
    
    perms_1stop = list(itertools.product(COMPOUNDS, repeat=2))
    
    for c1, c2 in perms_1stop:
        if c1 == c2: continue # Rule: Must use 2 compounds
        
        # Test Pit Window (Lap 20 to 40)
        for pit_lap in range(20, 41, 2):
            t1 = get_stint_time(model, encoder, driver, circuit, c1, 1, pit_lap)
            t2 = get_stint_time(model, encoder, driver, circuit, c2, pit_lap + 1, TOTAL_LAPS)
            
            # Use dynamic pit_loss
            total = t1 + t2 + pit_loss
            
            if total < best_1stop['Time']:
                best_1stop = {'Time': total, 'Desc': f"{c1} ({pit_lap}) -> {c2}"}
                
    m1 = int(best_1stop['Time'] // 60)
    s1 = best_1stop['Time'] % 60
    print(f"   🏆 Best 1-Stop: {best_1stop['Desc']}")
    print(f"      Time: {m1}m {s1:05.2f}s")

    # --- PART 2: OPTIMIZE 2-STOP ---
    print("\n2️⃣  Solving 2-Stop Strategies (Grandmaster Mode)...")
    best_2stop = {'Time': 999999, 'Desc': ''}
    
    perms_2stop = list(itertools.product(COMPOUNDS, repeat=3))
    
    for c1, c2, c3 in perms_2stop:
        if len(set([c1, c2, c3])) < 2: continue # Rule check
        
        # Test Coarse Pit Window
        for pit1 in range(12, 26, 4):
            t1 = get_stint_time(model, encoder, driver, circuit, c1, 1, pit1)
            
            for pit2 in range(pit1 + 15, 50, 4):
                t2 = get_stint_time(model, encoder, driver, circuit, c2, pit1 + 1, pit2)
                t3 = get_stint_time(model, encoder, driver, circuit, c3, pit2 + 1, TOTAL_LAPS)
                
                # Use dynamic pit_loss (x2)
                total = t1 + t2 + t3 + (pit_loss * 2)
                
                if total < best_2stop['Time']:
                    best_2stop = {'Time': total, 'Desc': f"{c1} ({pit1}) -> {c2} ({pit2}) -> {c3}"}

    m2 = int(best_2stop['Time'] // 60)
    s2 = best_2stop['Time'] % 60
    print(f"   🏆 Best 2-Stop: {best_2stop['Desc']}")
    print(f"      Time: {m2}m {s2:05.2f}s")

    # --- PART 3: THE VERDICT ---
    print("\n" + "="*40)
    diff = best_1stop['Time'] - best_2stop['Time']
    
    if diff > 0:
        print(f"🚀 VERDICT: 2-STOP WINS by {diff:.2f} seconds!")
        print(f"   Recommendation: Switch tyres twice to avoid the 'Cliff'.")
    else:
        print(f"🛡️ VERDICT: 1-STOP WINS by {abs(diff):.2f} seconds!")
        print(f"   Recommendation: Track position is king.")
    print("="*40)

if __name__ == "__main__":
    solve_battle()