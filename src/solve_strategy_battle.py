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
    
    # --- FIX: BROADCAST SCALARS TO LISTS ---
    # This prevents the "Mixing dicts" error on Cloud
    n_laps = len(laps)
    
    data = pd.DataFrame({
        'Driver': [driver] * n_laps,
        'Circuit': [circuit] * n_laps,
        'Compound': [tyre_set['compound']] * n_laps,
        'TyreLife': list(range(n_laps)),
        'LapNumber': laps,
        'Rainfall': [0] * n_laps,
        'FuelWeight': [110 * (1 - (l / TOTAL_LAPS)) for l in laps]
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
    # 1. Get Inventory for this scenario
    available_tyres = get_race_start_tyres(driver, strategy_mode=strategy_mode)
    tyre_indices = range(len(available_tyres))
    
    # --- 1-STOP OPTIMIZER ---
    best_1stop = {'Time': 999999, 'Desc': ''}
    for idx1, idx2 in itertools.permutations(tyre_indices, 2):
        set1, set2 = available_tyres[idx1], available_tyres[idx2]
        if set1['compound'] == set2['compound']: continue
        
        t1 = get_stint_time(model, encoder, driver, circuit, set1, 1, 25)
        t2 = get_stint_time(model, encoder, driver, circuit, set2, 26, TOTAL_LAPS)
        total = t1 + t2 + pit_loss + traffic_penalty
        
        if total < best_1stop['Time']:
            best_1stop = {'Time': total, 'Desc': f"{set1['compound']} ({set1['status']}) -> {set2['compound']} ({set2['status']})"}

    # --- 2-STOP OPTIMIZER ---
    best_2stop = {'Time': 999999, 'Desc': ''}
    
    valid_perms = [
        p for p in itertools.permutations(tyre_indices, 3) 
        if len({available_tyres[i]['compound'] for i in p}) >= 2
    ]

    for idx1, idx2, idx3 in valid_perms:
        set1, set2, set3 = available_tyres[idx1], available_tyres[idx2], available_tyres[idx3]
        
        t1 = get_stint_time(model, encoder, driver, circuit, set1, 1, 18)
        t2 = get_stint_time(model, encoder, driver, circuit, set2, 19, 38)
        t3 = get_stint_time(model, encoder, driver, circuit, set3, 39, TOTAL_LAPS)
        total = t1 + t2 + t3 + (pit_loss * 2) + (traffic_penalty * 2)
        
        if total < best_2stop['Time']:
            best_2stop = {'Time': total, 'Desc': f"{set1['compound']} ({set1['status']}) -> {set2['compound']} ({set2['status']}) -> {set3['compound']} ({set3['status']})"}

    # COMPARE
    diff = best_1stop['Time'] - best_2stop['Time']
    
    if diff > 0:
        return "2-STOP", best_2stop['Desc'], best_2stop['Time']
    else:
        return "1-STOP", best_1stop['Desc'], best_1stop['Time']

def solve_battle():
    # Helper for local testing
    pass

if __name__ == "__main__":
    solve_battle()