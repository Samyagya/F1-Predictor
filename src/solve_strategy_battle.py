import joblib
import pandas as pd
import os

# --- PATHS ---
MODEL_PATH = 'models/f1_baseline_model.pkl'
ENCODER_PATH = 'models/encoder.pkl'

def load_artifacts():
    """Loads the trained model and encoder."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(ENCODER_PATH):
        raise FileNotFoundError("Model artifacts not found. Please wait for the auto-updater to run.")
    
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    return model, encoder

def get_stint_time(model, encoder, driver_code, circuit, compound, laps, start_lap, traffic_factor=1.0):
    """
    Predicts the total time for a stint using the ML model.
    """
    # 1. Prepare Input Data (Must match auto_updater.py features EXACTLY)
    # Features: ['Driver', 'Circuit', 'Compound', 'TyreLife', 'LapNumber', 'Rainfall', 'FuelWeight']
    
    # We estimate average fuel for the stint (Linear burn approx)
    fuel_start = 110 - (start_lap * 1.7)
    fuel_end = 110 - ((start_lap + laps) * 1.7)
    avg_fuel = max(0, (fuel_start + fuel_end) / 2)
    
    # We predict the pace for the "average" lap in the stint
    avg_lap = start_lap + (laps / 2)
    avg_tyre_life = (laps / 2) + 1  # Assume fresh tyres at start of stint

    input_df = pd.DataFrame({
        'Driver': [driver_code],
        'Circuit': [circuit],
        'Compound': [compound],
        'TyreLife': [avg_tyre_life],
        'LapNumber': [avg_lap],
        'Rainfall': [0],  # <--- NEW: Defaults to Dry (0) for strategy planning
        'FuelWeight': [avg_fuel]
    })

    # 2. Encode Categoricals
    # The encoder was trained ONLY on ['Driver', 'Circuit', 'Compound']
    # We must transform those 3, then combine with the numericals.
    
    # Create a copy to avoid warnings
    df_encoded = input_df.copy()
    
    # Transform only the categorical columns
    cat_cols = ['Driver', 'Circuit', 'Compound']
    df_encoded[cat_cols] = encoder.transform(input_df[cat_cols])

    # 3. Predict Single Lap Pace
    # The model expects ALL columns: Cats + Nums
    feature_order = ['Driver', 'Circuit', 'Compound', 'TyreLife', 'LapNumber', 'Rainfall', 'FuelWeight']
    base_lap_time = model.predict(df_encoded[feature_order])[0]
    
    # 4. Calculate Total Stint Time
    # (Base Pace * Laps) + (Traffic Penalty)
    total_time = (base_lap_time * laps) * traffic_factor
    
    return total_time

def solve_scenario(model, encoder, driver_code, circuit, pit_loss, traffic, constraints, mode, fast_mode=False, tyre_constraints=None):
    """
    Calculates the best strategy (1-stop vs 2-stop).
    """
    strategies = []
    
    # --- STRATEGY OPTIONS ---
    # S = Soft, M = Medium, H = Hard
    options = [
        ['SOFT', 'MEDIUM'],          # 1-Stop
        ['MEDIUM', 'HARD'],          # 1-Stop
        ['SOFT', 'HARD'],            # 1-Stop
        ['SOFT', 'MEDIUM', 'SOFT'],  # 2-Stop Aggressive
        ['SOFT', 'MEDIUM', 'MEDIUM'],# 2-Stop Balanced
        ['MEDIUM', 'HARD', 'MEDIUM'] # 2-Stop Conservative
    ]
    
    # Race Distance (Approx 57 laps for Bahrain standard)
    TOTAL_LAPS = 57
    
    best_time = float('inf')
    best_strat = "Unknown"
    best_desc = "Analysis failed"

    for compounds in options:
        # Check tyre constraints (e.g. "No Softs")
        valid = True
        if tyre_constraints:
            for constraint in tyre_constraints:
                # If "No New Softs" and we use Soft, we check (simplified logic)
                for c in compounds:
                    if c == constraint['compound'] and constraint['limit'] == 0:
                        valid = False
        if not valid:
            continue

        # Split laps evenly for simplicity
        n_stops = len(compounds) - 1
        laps_per_stint = TOTAL_LAPS // len(compounds)
        
        current_time = 0
        current_lap = 0
        
        for i, compound in enumerate(compounds):
            # Last stint takes remainder laps
            if i == len(compounds) - 1:
                stint_len = TOTAL_LAPS - current_lap
            else:
                stint_len = laps_per_stint
            
            # Add Pit Loss for stops (not for race start)
            if i > 0:
                current_time += pit_loss
            
            # Calculate Driving Time
            stint_time = get_stint_time(model, encoder, driver_code, circuit, compound, stint_len, current_lap)
            current_time += stint_time
            current_lap += stint_len
            
        # Compare
        if current_time < best_time:
            best_time = current_time
            strategy_str = " -> ".join(compounds)
            best_strat = f"{len(compounds)-1} Stop ({strategy_str})"
            best_desc = f"Stints: ~{laps_per_stint} laps each. Total Time: {int(best_time//60)}m {int(best_time%60)}s"

    return best_strat, best_desc, best_time