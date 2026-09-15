# Feature: Machine Learning Lap Time Model

---

## What This Feature Does

The ML model is the analytical brain of the entire app. It is a regression model trained on historical F1 race lap data that predicts:

**Given a driver, circuit, tyre compound, tyre age, lap number, rainfall, and fuel weight — what lap time (in seconds) will the driver achieve?**

This single prediction capability is used by every tab:
- Tab 1 (Race Prediction): Predict lap times for all 22 drivers across 6 strategy templates
- Tab 2 (Workbench): Predict lap times for a chosen driver across 6 templates
- Tab 3 (AI Engineer): Called by the tool function to back every strategy answer with real numbers

---

## Files Involved

| File | Role |
|---|---|
| `src/train_baseline.py` | Offline training script (year-split, MAE evaluation) |
| `src/auto_updater.py` | Production retraining script (runs weekly via GitHub Actions) |
| `src/ingest_data.py` | Historical data download (one-time setup) |
| `src/process_data.py` | Merges raw CSVs into training-ready flat file |
| `src/add_feature.py` | Adds FuelWeight column to the processed dataset |
| `models/f1_baseline_model.pkl` | Serialised trained model |
| `models/encoder.pkl` | Serialised fitted OrdinalEncoder |
| `data/race_data.csv` | Flat lap dataset used for training |

---

## Tech Stack

| Component | Technology |
|---|---|
| Model Algorithm | scikit-learn GradientBoostingRegressor (auto_updater) / HistGradientBoostingRegressor (train_baseline) |
| Encoding | scikit-learn OrdinalEncoder (handle_unknown='use_encoded_value', unknown_value=-1) |
| Serialisation | joblib |
| Data Source | FastF1 F1 telemetry API |
| Data Processing | Pandas |

---

## Model Features (Inputs)

All 7 features are required at inference time, in this exact order:

| Feature | Type | Description |
|---|---|---|
| `Driver` | Categorical | 3-letter driver code (e.g. "VER", "HAM") |
| `Circuit` | Categorical | Circuit name (e.g. "Sakhir", "Silverstone") |
| `Compound` | Categorical | Tyre type: SOFT, MEDIUM, HARD, INTERMEDIATE, WET |
| `TyreLife` | Numeric | How many laps this tyre set has been used |
| `LapNumber` | Numeric | The current lap in the race (1-70) |
| `Rainfall` | Binary | 0 = dry, 1 = wet |
| `FuelWeight` | Numeric | Estimated fuel remaining in kg (starts ~110, ends ~0) |

---

## Model Target (Output)

| Target | Type | Unit |
|---|---|---|
| `LapTime` | Float | Seconds (e.g. 91.234 for 1:31.234) |

---

## Training Strategy

- **Training data:** 2023-2024 race seasons
- **Test data:** 2025 race season (model has never seen this data)
- **Data filtering:** Only clean green-flag laps used (no pit laps, safety car laps, or crashes)
- **Evaluation metric:** Mean Absolute Error (MAE) in seconds
- **Success threshold:** MAE < 2.0 seconds

---

## Inference Pattern (in solve_strategy_battle.py)

Rather than predicting every lap individually, the strategy engine uses a **stint-average approximation**:

1. Calculate average fuel for the stint: `(fuel_start + fuel_end) / 2`
2. Calculate average lap in the stint: `start_lap + (laps / 2)`
3. Calculate average tyre age: `(laps / 2) + 1`
4. Predict **one** lap time using these averages
5. Multiply by the number of laps in the stint to get total stint time

This approximation is ~10x faster than per-lap prediction while maintaining high accuracy for strategy comparison purposes.

---

## Decisions Made for This Feature

### Why GradientBoostingRegressor over RandomForest or LinearRegression?
Gradient boosting consistently outperforms random forest on structured tabular data with complex interactions (e.g., the interaction between TyreLife and Compound has a non-linear "cliff" shape). Linear regression cannot capture these non-linearities.

### Why not a neural network?
With 7 input features and tens of thousands of rows, a neural network would not provide significantly better accuracy than gradient boosting, but would be much slower to train weekly and harder to debug. Gradient boosting also has native support for mixed categorical/numerical inputs.

### Why OrdinalEncoder instead of OneHotEncoder?
With 20+ drivers, 22 circuits, and 5 compounds, OneHotEncoding would create ~50 additional binary columns. Gradient boosting trees handle ordinal-encoded categories natively (they split on threshold values). The compact encoding keeps training fast and the model file small.

### Why encode only the first 3 columns (Driver, Circuit, Compound)?
The encoder was fitted on only these 3 categorical columns in `auto_updater.py`. The remaining 4 features (TyreLife, LapNumber, Rainfall, FuelWeight) are already numeric. This matches the inference code in `solve_strategy_battle.py` which transforms only cat_cols = ['Driver', 'Circuit', 'Compound'].

### Why hardcode FuelWeight as `110 - (LapNumber * 1.7)` instead of the race-length formula?
The simple linear formula `110kg - 1.7kg/lap` is a physics approximation that works for most F1 circuits (~57-70 laps). In `add_feature.py` (offline), the actual total laps per race is computed from the data. At inference time, 1.7 kg/lap is used as a universal constant for speed.

### Why train a fresh model each week instead of incrementally updating?
scikit-learn's GradientBoosting does not support `partial_fit()` (incremental learning). A full retrain is required when new data is added. Given the dataset size and available compute (GitHub Actions ubuntu-latest), a full retrain takes under 60 seconds.
