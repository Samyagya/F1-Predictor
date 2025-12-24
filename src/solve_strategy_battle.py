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
    # ... (Keep this function exactly the same as before) ...
    laps = list(range(start_lap, end_lap + 1))
    if not laps: return 0
    
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

def solve_scenario(model, encoder, driver, circuit, pit_loss, traffic_penalty, scenario_name, strategy_mode, fast_mode=False, tyre_constraints=[]):
    """
    Runs optimization with optional tyre constraints.
    tyre_constraints = [{'compound': 'MEDIUM', 'status': 'NEW', 'limit': 0}, ...]
    """
    # 1. Get Base Inventory (Standard Q3)
    base_tyres = get_race_start_tyres(driver, strategy_mode=strategy_mode)
    
    # 2. --- APPLY CUSTOM USER CONSTRAINTS ---
    available_tyres = []
    if not tyre_constraints:
        available_tyres = base_tyres
    else:
        # Group base tyres by type to apply limits
        tyre_groups = {'SOFT_NEW': [], 'SOFT_USED': [], 'MEDIUM_NEW': [], 'MEDIUM_USED': [], 'HARD_NEW': [], 'HARD_USED': []}
        for t in base_tyres:
            key = f"{t['compound']}_{t['status']}"
            if key in tyre_groups: tyre_groups[key].append(t)

        # Apply limits defined by user
        for const in tyre_constraints:
            key = f"{const['compound']}_{const['status']}"
            limit = const['limit']
            if key in tyre_groups:
                # Slice the list to keep only up to 'limit' tyres
                tyre_groups[key] = tyre_groups[key][:limit]

        # Rebuild final available list
        for group in tyre_groups.values():
            available_tyres.extend(group)

    # Ensure we still have enough tyres to run a strategy
    if len(available_tyres) < 3:
        return "INVALID", "Too few tyres available based on user constraints.", 999999

    tyre_indices = range(len(available_tyres))

    # --- TURBO MODE OPTIMIZATION ---
    if fast_mode:
        best_indices = []
        seen_compounds = set()
        # Sort by age (freshest first) to pick best ones
        sorted_indices = sorted(tyre_indices, key=lambda i: available_tyres[i]['age'])
        for idx in sorted_indices:
            comp = available_tyres[idx]['compound']
            # We want at least one of each available compound
            if comp not in seen_compounds:
                best_indices.append(idx)
                seen_compounds.add(comp)
            # Allow up to 4 total tyres in the pool for flexibility
            elif len(best_indices) < 4: 
                best_indices.append(idx)
        tyre_indices = best_indices

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

if __name__ == "__main__":
    pass