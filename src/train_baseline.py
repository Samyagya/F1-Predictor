import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import OrdinalEncoder
from sklearn.metrics import mean_absolute_error
import joblib  # To save the trained model
import os

# --- CONFIGURATION ---
DATA_PATH = os.path.join('data', 'processed', 'f1_training_data.csv')
MODEL_DIR = 'models'
os.makedirs(MODEL_DIR, exist_ok=True)

def train_model():
    print("1. Loading Data...")
    df = pd.read_csv(DATA_PATH)
    
    # --- PREPROCESSING ---
    # We only want to train on valid racing laps
    # Remove out-laps (LapTime > 110% of median) to remove crashes/safety cars
    median_time = df['LapTime_Seconds'].median()
    df = df[df['LapTime_Seconds'] < median_time * 1.15]
    
    print(f"   Training on {len(df)} clean racing laps.")

    # Select Features (Inputs) and Target (Output)
    # We want to predict 'LapTime_Seconds' based on:
    features = ['Driver', 'Circuit', 'Compound', 'TyreLife', 'LapNumber', 'Rainfall']
    target = 'LapTime_Seconds'

    # Handle Text Columns (Driver, Circuit, Compound)
    # Machines only understand numbers. We use OrdinalEncoder to convert "Hamilton" -> 44, "Soft" -> 1
    print("2. Encoding Features...")
    encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    
    # We split data strictly by YEAR to simulate predicting the future
    # Train: 2023 & 2024
    # Test: 2025 (The AI has never seen this year)
    train_data = df[df['Year'] < 2025].copy()
    test_data = df[df['Year'] == 2025].copy()
    
    print(f"   Train Set: {len(train_data)} laps (2023-2024)")
    print(f"   Test Set:  {len(test_data)} laps (2025)")

    # Transform text to numbers
    X_train = encoder.fit_transform(train_data[features])
    y_train = train_data[target]
    
    X_test = encoder.transform(test_data[features])
    y_test = test_data[target]

    # --- TRAINING ---
    print("3. Training Model (Gradient Boosting)...")
    model = HistGradientBoostingRegressor(
        max_iter=100, 
        learning_rate=0.1, 
        max_depth=10, 
        random_state=42
    )
    model.fit(X_train, y_train)
    print("   Model Trained!")

    # --- EVALUATION ---
    print("4. Evaluating Performance...")
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    
    print(f"\n=== REPORT CARD ===")
    print(f"Mean Absolute Error (MAE): {mae:.3f} seconds")
    print("Interpretation: On average, the AI's guess is within")
    print(f"{mae:.3f} seconds of the real lap time.")
    
    # Save the Brain
    joblib.dump(model, os.path.join(MODEL_DIR, 'f1_baseline_model.pkl'))
    joblib.dump(encoder, os.path.join(MODEL_DIR, 'encoder.pkl'))
    print(f"\nModel saved to '{MODEL_DIR}/f1_baseline_model.pkl'")

if __name__ == "__main__":
    train_model()