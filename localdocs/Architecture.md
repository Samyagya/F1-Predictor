# Architecture — F1 2026 Strategy Oracle

---

## 1. App Flow

```
User opens Streamlit App (app.py)
         |
         +-- Tab 1: Next Race Predictor
         |       |
         |       +-> calendar_utils.py  [get_next_race()]
         |       +-> solve_strategy_battle.py  [load_artifacts(), solve_scenario()]
         |       +-> physics.py  [get_pit_loss()]
         |       +-> Display results in UI (podium + table)
         |
         +-- Tab 2: Strategy Workbench
         |       |
         |       +-> User picks Driver + Circuit
         |       +-> solve_strategy_battle.py  [solve_scenario() x3 modes]
         |       +-> Display 3 strategy reports
         |
         +-- Tab 3: AI Race Engineer
                 |
                 +-> llm_agent.py  [F1Agent.ask()]
                         |
                         +-> Groq API (Llama 3.3 70B) — First call
                         +-> run_strategy_simulation() [Tool Call]
                                 |
                                 +-> physics.py [get_pit_loss()]
                                 +-> solve_strategy_battle.py [solve_scenario()]
                         +-> Groq API (Llama 3.3 70B) — Second call (final answer)
```

### Offline Data Pipeline (GitHub Actions — every Monday)
```
auto_updater.py
    |
    +-> fastf1 [fetch last completed race session]
    +-> Append to data/race_data.csv
    +-> Retrain GradientBoostingRegressor
    +-> Save models/f1_baseline_model.pkl + models/encoder.pkl
    +-> Git auto-commit
```

---

## 2. Folder and File Structure

```
F1-Predictor/
|
|-- app.py                        # Main Streamlit entry point. All 3 tabs live here.
|
|-- requirements.txt              # Python dependencies for the Streamlit app
|
|-- data/
|   |-- race_data.csv             # Flat lap-level dataset (auto-updated weekly)
|   |-- .gitkeep                  # Ensures empty data/ folder is tracked by git
|
|-- models/
|   |-- f1_baseline_model.pkl     # Trained GradientBoosting model (binary, joblib)
|   |-- encoder.pkl               # Fitted OrdinalEncoder for categorical features
|
|-- src/
|   |-- __init__.py               # Makes src a Python package
|   |-- physics.py                # Pit loss lookup table + tyre cliff penalty formula
|   |-- calendar_utils.py         # 2026 race calendar + get_next_race() logic
|   |-- solve_strategy_battle.py  # CORE: loads model, evaluates 6 strategy templates
|   |-- llm_agent.py              # Groq LLM agent + function-calling tool wrapper
|   |-- ai_analyst.py             # Earlier regex-based NLU analyst (legacy, not used in app.py)
|   |-- auto_updater.py           # Weekly data fetch + model retraining script
|   |-- ingest_data.py            # One-time bulk historical data ingestion (2023-2025)
|   |-- process_data.py           # Processes raw CSVs into training-ready flat file
|   |-- add_feature.py            # Adds FuelWeight column to processed data
|   |-- train_baseline.py         # Standalone model training script (offline)
|   |-- predict_lap.py            # CLI tool: predicts a single lap time interactively
|   |-- simulate_race.py          # CLI tool: lap-by-lap race simulation with print output
|   |-- solve_strategy.py         # CLI tool: finds optimal 1-stop pit lap
|   |-- solve_2stop.py            # CLI tool: brute-force 2-stop optimiser
|   |-- tyre_strategy.py          # Tyre inventory manager (simulates qualifying tyre wear)
|   |-- visualize.py              # Generates tyre degradation scatter plot PNG
|   |-- check_name.py             # CLI utility: prints all valid driver/circuit/compound names
|
|-- .github/
|   |-- workflows/
|       |-- weekly_update.yml     # GitHub Actions CRON job for weekly data update
|
|-- localdocs/                    # Project documentation (this folder)
|   |-- PRD.md
|   |-- Architecture.md
|   |-- rules.md
|   |-- Phases.md
|   |-- design.md
|   |-- memory.md
|   |-- features/
|       |-- next_race_prediction.md
|       |-- strategy_workbench.md
|       |-- ai_race_engineer.md
|       |-- auto_updater.md
|       |-- ml_model.md
|       |-- physics_engine.md
|
|-- screenshots/                  # App screenshots for README
|-- check_data.png                # Output of visualize.py
```

---

## 3. Tech Stack

### Frontend / UI
| Technology | Version | Role |
|---|---|---|
| **Streamlit** | latest | Web framework, tabs, widgets, state |
| **Pandas** | latest | DataFrames for display and data passing |

### AI / LLM Layer
| Technology | Role |
|---|---|
| **Groq API** | High-speed inference provider |
| **Llama 3.3 70B Versatile** | The LLM model — understands queries + orchestrates tool calls |
| **Function Calling (Groq)** | LLM decides when to call the simulation tool |

### Machine Learning / Physics
| Technology | Role |
|---|---|
| **FastF1** | Pulls official F1 session data (laps, telemetry, weather) |
| **Scikit-Learn (GradientBoostingRegressor / HistGradientBoostingRegressor)** | Lap time prediction model |
| **Scikit-Learn (OrdinalEncoder)** | Encodes Driver, Circuit, Compound as integers |
| **Joblib** | Model serialisation/deserialisation (.pkl files) |

### DevOps / Automation
| Technology | Role |
|---|---|
| **GitHub Actions** | Weekly CRON job runner |
| **stefanzweifel/git-auto-commit-action** | Auto-commits model + data files post-retraining |
| **Git** | Version control |

---

## 4. Data Flow

```
Raw F1 Data (FastF1 API)
        |
        v
auto_updater.py / ingest_data.py
        |
        v
data/race_data.csv
[Columns: Driver, Circuit, Compound, TyreLife, LapNumber, Rainfall, FuelWeight, LapTime]
        |
        v
OrdinalEncoder  (Driver, Circuit, Compound -> integers)
        |
        v
GradientBoostingRegressor.fit(X, y)
        |
        v
models/f1_baseline_model.pkl + models/encoder.pkl
        |
        v
solve_strategy_battle.py :: get_stint_time()
[Predicts average lap pace for a stint, multiplied by stint length]
        |
        v
solve_scenario()
[Tries 6 compound strategies, picks minimum total time]
        |
        v
app.py / llm_agent.py
[Renders results in UI or passes to LLM for natural language response]
```

---

## 5. Key Design Decisions

| Decision | Rationale |
|---|---|
| Streamlit over Flask/FastAPI | Zero boilerplate UI, ideal for data-heavy Python apps |
| Groq over OpenAI | Much faster inference (~10x), generous free tier |
| GradientBoosting over Neural Network | Interpretable, works well on tabular data, fast to train |
| OrdinalEncoder over OneHotEncoder | Avoids feature explosion with many driver/circuit categories |
| Hardcoded 2026 Calendar | FastF1 may not have 2026 schedule; avoids dependency on live calendar API |
| Stint-average approximation | Computing average lap rather than lap-by-lap keeps inference fast for 6 strategy x 22 driver grid simulation |
