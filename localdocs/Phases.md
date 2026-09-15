# Phases — F1 2026 Strategy Oracle

This document breaks the project into distinct build phases for systematic development.
Each phase has a clear goal, deliverables, and completion criteria.

---

## Phase 0: Environment Setup
**Status: COMPLETE**

### Goal
Set up the development environment and project skeleton.

### Tasks
- [x] Create GitHub repository
- [x] Set up virtual environment with requirements.txt
- [x] Create `src/` package with `__init__.py`
- [x] Create `data/` and `models/` directories with `.gitkeep`
- [x] Add `.gitignore` (ignore `cache/`, `__pycache__/`, `.env`)

### Deliverables
- Project folder structure
- requirements.txt (streamlit, pandas, scikit-learn, joblib, groq)
- Working Python environment

---

## Phase 1: Data Ingestion
**Status: COMPLETE**

### Goal
Download and store historical F1 race data from 2023-2025 using FastF1.

### Tasks
- [x] Write `src/ingest_data.py` to bulk-download race sessions (2023-2025)
- [x] Extract lap data, weather data, and race results per race
- [x] Save to `data/raw/` folder with race ID naming convention
- [x] Write `src/process_data.py` to merge raw files into a flat training CSV
- [x] Write `src/add_feature.py` to compute FuelWeight column
- [x] Validate data with `src/check_name.py` and `src/visualize.py`

### Deliverables
- `data/raw/` — raw per-race CSVs (laps, weather, results)
- `data/processed/f1_training_data_v2.csv` — clean training dataset

### Key Columns in Final Dataset
`Driver, Circuit, Compound, TyreLife, LapNumber, Rainfall, FuelWeight, LapTime_Seconds`

---

## Phase 2: Machine Learning Model
**Status: COMPLETE**

### Goal
Train a regression model to predict lap times from tyre and fuel state.

### Tasks
- [x] Write `src/train_baseline.py` using HistGradientBoostingRegressor
- [x] Encode Driver/Circuit/Compound with OrdinalEncoder
- [x] Split by year (train: 2023-2024, test: 2025)
- [x] Evaluate with Mean Absolute Error (MAE)
- [x] Save model and encoder to `models/`
- [x] Validate predictions with `src/predict_lap.py`

### Deliverables
- `models/f1_baseline_model.pkl`
- `models/encoder.pkl`

### Success Criteria
- MAE < 2.0 seconds on 2025 test data

---

## Phase 3: Physics Engine and Strategy Solver
**Status: COMPLETE**

### Goal
Build the core simulation layer that converts ML pace predictions into full race strategy outcomes.

### Tasks
- [x] Write `src/physics.py` — pit lane loss lookup table (22 circuits) + tyre cliff penalty
- [x] Write `src/tyre_strategy.py` — tyre inventory simulator (Q1/Q2/Q3 qualifying modes)
- [x] Write `src/simulate_race.py` — lap-by-lap CLI race simulator
- [x] Write `src/solve_strategy.py` — 1-stop pit window optimiser
- [x] Write `src/solve_2stop.py` — brute-force 2-stop compound + pit lap optimiser
- [x] Write `src/solve_strategy_battle.py` — production strategy evaluator (6 templates, fast mode)

### Deliverables
- A function `solve_scenario()` that returns (strategy_name, description, race_time_seconds)

### Key Design: Strategy Templates
1. SOFT -> MEDIUM (1-stop)
2. MEDIUM -> HARD (1-stop)
3. SOFT -> HARD (1-stop)
4. SOFT -> MEDIUM -> SOFT (2-stop Aggressive)
5. SOFT -> MEDIUM -> MEDIUM (2-stop Balanced)
6. MEDIUM -> HARD -> MEDIUM (2-stop Conservative)

---

## Phase 4: Streamlit Frontend — Basic Tabs
**Status: COMPLETE**

### Goal
Build the initial Streamlit app with Next Race and Workbench tabs.

### Tasks
- [x] Create `app.py` with `st.set_page_config()`
- [x] Implement Tab 1: Next Race Predictor (full 22-driver grid simulation)
- [x] Implement Tab 2: Strategy Workbench (3 qualifying mode scenarios)
- [x] Add DRIVERS dict (full 2026 grid with 3-letter codes)
- [x] Add CIRCUITS list (22 circuits)
- [x] Add `format_time()` helper
- [x] Handle driver-skill bias for race prediction

### Deliverables
- Working app.py with Tabs 1 and 2

---

## Phase 5: AI Race Engineer (LLM Integration)
**Status: COMPLETE**

### Goal
Add a conversational AI chatbot that uses function calling to run real simulations.

### Tasks
- [x] Write `src/llm_agent.py` with Groq client and F1Agent class
- [x] Define `run_strategy_simulation` as a Groq tool (function calling)
- [x] Implement two-turn conversation: first call decides tool use, second call generates final answer
- [x] Handle API key via Streamlit secrets or sidebar input
- [x] Add Tab 3 to app.py with chat_message UI
- [x] Persist chat history in st.session_state
- [x] Add tyre constraint parsing (no new softs, no new mediums, etc.)

### Deliverables
- Tab 3 fully functional AI chatbot
- F1Agent class that wraps Groq API

---

## Phase 6: Automatic Weekly Update (CI/CD)
**Status: COMPLETE**

### Goal
Automate weekly data fetching and model retraining via GitHub Actions.

### Tasks
- [x] Write `src/auto_updater.py` with FastF1 fetch + retrain logic
- [x] Add retry logic (3 attempts with 60s delay) for FastF1 failures
- [x] Handle missing Rainfall column gracefully
- [x] Write `.github/workflows/weekly_update.yml`
- [x] Configure CRON schedule (Monday 14:00 UTC)
- [x] Configure git-auto-commit-action to push model + data changes

### Deliverables
- Fully automated pipeline that runs without manual intervention

---

## Phase 7: Future Improvements (Planned / Not Started)

### 7.1 UI/UX Polish
- [ ] Add dark F1 theme with team colours
- [ ] Replace progress bar with animated lap counter graphic
- [ ] Add tyre compound colour indicators (Red=Soft, Yellow=Medium, White=Hard)
- [ ] Mobile responsive layout

### 7.2 Model Improvements
- [ ] Add circuit-specific lap count (currently hardcoded to 57)
- [ ] Model wet race conditions (currently Rainfall=0 always at prediction time)
- [ ] Per-driver degradation profiles
- [ ] Safety car probability integration

### 7.3 Feature Expansions
- [ ] Live qualifying pace input for same-day race predictions
- [ ] Head-to-head strategy comparison (two drivers on same chart)
- [ ] Exportable PDF race strategy report
- [ ] Historical race result archive tab
