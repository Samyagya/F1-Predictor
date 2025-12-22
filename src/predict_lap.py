import pandas as pd
import joblib
import os
import warnings

# Silence warnings
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
MODEL_PATH = os.path.join('models', 'f1_baseline_model.pkl')
ENCODER_PATH = os.path.join('models', 'encoder.pkl')

def load_artifacts():
    if not os.path.exists(MODEL_PATH):
        print("ERROR: Model not found! Did you run train_baseline.py?")
        exit()
    
    print("Loading AI Brain...")
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    return model, encoder

def get_user_input():
    print("\n--- F1 RACE PREDICTOR (v1) ---")
    print("Enter the scenario details below:\n")
    
    # We strip spaces to avoid "VER " errors
    driver = input("Driver (e.g., VER, HAM): ").strip()
    circuit = input("Circuit (e.g., Sakhir, Monza): ").strip()
    compound = input("Tyre Compound (SOFT, MEDIUM, HARD): ").strip().upper()
    
    try:
        lap_number = int(input("Lap Number (1-70): "))
        tyre_life = int(input("Tyre Age (Laps driven on these tyres): "))
    except ValueError:
        print("❌ Error: Lap Number and Tyre Age must be numbers!")
        return None

    is_raining = input("Is it raining? (yes/no): ").lower().strip() == 'yes'
    
    # Auto-calculate Fuel Weight (Physics approximation)
    total_laps_avg = 57
    fuel_weight = 110 * (1 - (lap_number / total_laps_avg))
    if fuel_weight < 0: fuel_weight = 0
    
    # Create DataFrame with EXACTLY the columns the model expects
    data = {
        'Driver': [driver],
        'Circuit': [circuit],
        'Compound': [compound],
        'TyreLife': [tyre_life],
        'LapNumber': [lap_number],
        'Rainfall': [1 if is_raining else 0],
        'FuelWeight': [fuel_weight]
    }
    
    return pd.DataFrame(data)

def predict():
    model, encoder = load_artifacts()
    
    while True:
        try:
            # 1. Get Input
            input_df = get_user_input()
            if input_df is None: continue
            
            # 2. Encode (Transform ALL columns, just like in training)
            # The encoder expects 7 columns. We give it 7 columns.
            encoded_data = encoder.transform(input_df)
            
            # 3. Predict
            prediction = model.predict(encoded_data)[0]
            
            # 4. Show Result
            minutes = int(prediction // 60)
            seconds = prediction % 60
            
            print(f"\n🏎️  PREDICTED LAP TIME: {minutes}:{seconds:06.3f}")
            print(f"    (Raw Seconds: {prediction:.3f}s)")
            
        except ValueError as e:
            # Check if the error is actually about unknown categories
            err_msg = str(e)
            if "unknown categories" in err_msg or "Found unknown" in err_msg:
                print(f"\n❌ Error: The AI has never seen that Driver, Circuit, or Compound before.")
                print("   Check your spelling! Use 'check_names.py' to see valid options.")
            else:
                print(f"\n❌ Unexpected Error: {e}")
                
        except Exception as e:
            print(f"\n❌ Critical Error: {e}")
            
        # Ask to continue
        if input("\nPredict again? (y/n): ").lower() != 'y':
            break

if __name__ == "__main__":
    predict()