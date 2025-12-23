import pandas as pd
import joblib
import os
import itertools
import warnings

# --- IMPORTS ---
try:
    from src.physics import get_pit_loss, calculate_tyre_cliff_penalty
    from src.tyre_strategy import get_race_start_tyres
except ImportError:
    from physics import get_pit_loss, calculate_tyre_cliff_penalty
    from tyre_strategy import get_race_start_tyres

warnings.filterwarnings('ignore')

# --- CONFIG ---
MODEL_PATH = os.path.join('models', 'f1_baseline_model.pkl')
ENCODER_PATH = os.path.join('models', 'encoder.pkl')
TOTAL_LAPS = 57

def load_artifacts():
    if not os.path.exists(MODEL_PATH):
        return None, None
    return joblib.load(MODEL_PATH), joblib.load(ENCODER_PATH)

def get_stint_time(model, encoder, driver, circuit, tyre_set, start_lap, end_lap):
    laps = list(range(start_lap, end_lap + 1))
    if not laps: return 0
    
    data = pd.DataFrame({
        'Driver': driver, 'Circuit': circuit, 'Compound': tyre_set['compound'],
        'TyreLife': range(len(laps)), 'LapNumber': laps,
        'Rainfall': 0, 'FuelWeight': [110 * (1 - (l / TOTAL_LAPS)) for l in laps]
    })
    data.loc[data['FuelWeight'] < 0, 'FuelWeight'] = 0
    
    base_predictions = model.predict(encoder.transform(data))
    
    total_stint_time = 0
    for i, lap_time in enumerate(base_predictions):
        current_tyre_age = i + tyre_set['age']
        penalty = calculate_tyre_cliff_penalty(tyre_set['compound'], current_tyre_age)
        total_stint_time += (lap_time + penalty)
        
    return total_stint_time

def solve_scenario(model, encoder, driver, circuit, pit_loss, traffic_penalty, scenario_name, strategy_mode):
    """
    Runs a single optimization loop for a specific Qualifying Scenario.
    """
    print(f"\n   📍 SCENARIO: {scenario_name}")
    
    # 1. Get Inventory for this scenario
    available_tyres = get_race_start_tyres(driver, strategy_mode=strategy_mode)
    tyre_indices = range(len(available_tyres))
    
    # Debug: Show top inventory item
    top_tyre = available_tyres[3] # Usually the first soft
    print(f"      Inventory Status: Softs are {top_tyre['status']} (Age {top_tyre['age']})")

    # --- 1-STOP OPTIMIZER ---
    best_1stop = {'Time': 999999, 'Desc': ''}
    for idx1, idx2 in itertools.permutations(tyre_indices, 2):
        set1, set2 = available_tyres[idx1], available_tyres[idx2]
        if set1['compound'] == set2['compound']: continue
        
        # Fast check at Lap 25
        t1 = get_stint_time(model, encoder, driver, circuit, set1, 1, 25)
        t2 = get_stint_time(model, encoder, driver, circuit, set2, 26, TOTAL_LAPS)
        total = t1 + t2 + pit_loss + traffic_penalty
        
        if total < best_1stop['Time']:
            best_1stop = {'Time': total, 'Desc': f"{set1['status']} {set1['compound']} -> {set2['status']} {set2['compound']}"}

    # --- 2-STOP OPTIMIZER ---
    best_2stop = {'Time': 999999, 'Desc': ''}
    
    # Filter for valid 3-set combos (must have 2 diff compounds)
    valid_perms = []
    for p in itertools.permutations(tyre_indices, 3):
        sets = [available_tyres[i] for i in p]
        if len({s['compound'] for s in sets}) >= 2:
            valid_perms.append(p)

    for idx1, idx2, idx3 in valid_perms:
        set1, set2, set3 = available_tyres[idx1], available_tyres[idx2], available_tyres[idx3]
        
        # Fixed stops for speed
        t1 = get_stint_time(model, encoder, driver, circuit, set1, 1, 18)
        t2 = get_stint_time(model, encoder, driver, circuit, set2, 19, 38)
        t3 = get_stint_time(model, encoder, driver, circuit, set3, 39, TOTAL_LAPS)
        total = t1 + t2 + t3 + (pit_loss * 2) + (traffic_penalty * 2)
        
        if total < best_2stop['Time']:
            best_2stop = {'Time': total, 'Desc': f"{set1['status']} {set1['compound']} -> {set2['status']} {set2['compound']} -> {set3['status']} {set3['compound']}"}

    # COMPARE
    diff = best_1stop['Time'] - best_2stop['Time']
    
    if diff > 0:
        win_time = best_2stop['Time']
        print(f"      🏆 Winner: 2-STOP ({best_2stop['Desc']})")
        print(f"         Time: {int(win_time//60)}m {win_time%60:.2f}s (Beats 1-Stop by {diff:.2f}s)")
    else:
        win_time = best_1stop['Time']
        print(f"      🏆 Winner: 1-STOP ({best_1stop['Desc']})")
        print(f"         Time: {int(win_time//60)}m {win_time%60:.2f}s (Beats 2-Stop by {abs(diff):.2f}s)")

def solve_battle():
    model, encoder = load_artifacts()
    
    print("\n--- 🏁 STRATEGY REPORT GENERATOR (v5: MULTI-SCENARIO) ---")
    driver = input("Driver (e.g., VER): ").strip()
    circuit = input("Circuit (e.g., Sakhir): ").strip()
    
    pit_loss = get_pit_loss(circuit)
    traffic = 1.5
    
    print(f"\nGenerating Full Strategic Report for {driver} at {circuit}...")
    print("="*60)
    
    # SCENARIO 1: The "Star Performer" (Q3)
    solve_scenario(model, encoder, driver, circuit, pit_loss, traffic, 
                   "QUALIFIED P1-P10 (Used Softs)", "Standard Q3")
    
    print("-" * 60)
    
    # SCENARIO 2: The "Midfield Battle" (Q2)
    solve_scenario(model, encoder, driver, circuit, pit_loss, traffic, 
                   "QUALIFIED P11-P15 (Mixed Softs)", "Knocked out in Q2")

    print("-" * 60)
    
    # SCENARIO 3: The "Recovery Drive" (Q1)
    solve_scenario(model, encoder, driver, circuit, pit_loss, traffic, 
                   "QUALIFIED P16-P20 (Fresh Softs)", "Knocked out in Q1")
    
    print("="*60)

if __name__ == "__main__":
    solve_battle()