# Complete User Guide — F1 2026 Strategy Oracle

Welcome to the **F1 2026 Strategy Oracle**! This guide is written for anyone—even with **zero programming experience**—who wants to run, use, explore, or retrain this Formula 1 prediction and strategy intelligence system.

---

## 📑 Table of Contents
1. [⚡ Quick Start: Run the Model Right Now (In 60 Seconds)](#1--quick-start-run-the-model-right-now-in-60-seconds)
2. [💻 System Prerequisites & Setup](#2--system-prerequisites--setup)
3. [📖 Command-by-Command Reference (What Every Script Does)](#3--command-by-command-reference-what-every-script-does)
4. [🖥️ Exploring the Interactive Dashboard (Streamlit App)](#4-️-exploring-the-interactive-dashboard-streamlit-app)
5. [🤖 Setting Up the AI Race Engineer (Groq API Key)](#5--setting-up-the-ai-race-engineer-groq-api-key)
6. [🔬 Full Pipeline from Scratch (Ingestion to Retraining)](#6--full-pipeline-from-scratch-ingestion-to-retraining)
7. [🏎️ Running Standalone CLI Simulation Tools](#7-️-running-standalone-cli-simulation-tools)
8. [🔄 Automated Weekly Updates (GitHub Actions)](#8--automated-weekly-updates-github-actions)
9. [❓ Troubleshooting & FAQ for Beginners](#9--troubleshooting--faq-for-beginners)

---

## 1. ⚡ Quick Start: Run the Model Right Now (In 60 Seconds)

If your machine already has Python installed, **you do not need to train anything**. A verified, retrained machine learning model is already saved in the repository (`models/f1_baseline_model.pkl` and `models/encoder.pkl`).

### Step 1: Open your terminal
- On **Windows**: Press `Win + R`, type `powershell` or `cmd`, and press Enter. Navigate to the project folder:
  ```powershell
  cd c:\Users\samya\Desktop\F1-Predictor
  ```
- Or right-click inside the `F1-Predictor` folder in File Explorer and choose **"Open in Terminal"**.

### Step 2: Install required packages (first time only)
```powershell
python -m pip install -r requirements.txt
```
*(On Windows, using `python -m pip` avoids PATH issues where typing `pip` alone fails).*

### Step 3: Launch the interactive web app
```powershell
python -m streamlit run app.py
```
*(Alternatively: `streamlit run app.py`)*

### Step 4: View the app
Your default browser will automatically open to:
```
http://localhost:8501
```
You can now immediately view:
- **🏆 Tab 1 — Next Race Prediction:** Predicts the upcoming 2026 Grand Prix winner and podium.
- **🛠️ Tab 2 — Strategy Workbench:** Test 1-stop vs 2-stop strategies, qualifying tyre penalties (Q1/Q2/Q3), and traffic factors.
- **🤖 Tab 3 — AI Race Engineer:** Conversational AI strategy assistant (enter a free Groq API key in the sidebar).

To stop the web server at any time, go to your terminal window and press **`Ctrl + C`**.

---

## 2. 💻 System Prerequisites & Setup

If you are setting up the project on a new computer, follow these steps step-by-step:

### A. Check Python Installation
Make sure Python 3.9, 3.10, or 3.11 is installed:
```powershell
python --version
```
- **Expected Output:** `Python 3.9.x` (or 3.10.x / 3.11.x).
- If not installed, download Python from [python.org](https://www.python.org/downloads/) and **ensure you check the box that says "Add Python to PATH"** during installation.

### B. (Optional but Recommended) Create a Virtual Environment
A virtual environment keeps the project libraries isolated so they do not conflict with other software on your PC:
```powershell
# 1. Create a virtual environment named 'venv'
python -m venv venv

# 2. Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate
```
*(When activated, you will see `(venv)` at the beginning of your terminal prompt).*

### C. Install All Dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you plan to fetch new live F1 telemetry data or retrain using the auto-updater, install `fastf1` as well:
```powershell
python -m pip install fastf1
```

---

## 3. 📖 Command-by-Command Reference (What Every Script Does)

Here is a plain-English reference explaining what each command does, what files it touches, and when you should run it:

| Command | What It Does | Input Files | Output Files |
|---|---|---|---|
| `python -m streamlit run app.py` | Launches the interactive browser UI for predictions, strategy optimization, and AI chat. | `models/*.pkl`, `src/*.py` | None (reads only) |
| `python src/predict_lap.py` | Interactive terminal tool asking you for driver, circuit, tyre compound, tyre age, and fuel load, then predicting the exact lap time. | `models/f1_baseline_model.pkl`, `models/encoder.pkl` | None (prints to console) |
| `python src/simulate_race.py` | Simulates an entire 57-lap Grand Prix lap-by-lap, showing tyre degradation and pit stop timing. | `models/f1_baseline_model.pkl`, `models/encoder.pkl` | None (prints lap table) |
| `python src/solve_strategy.py` | Brute-force tests every possible 1-stop lap window to find the fastest pit stop lap. | `models/f1_baseline_model.pkl`, `models/encoder.pkl` | None (prints best lap) |
| `python src/solve_2stop.py` | Evaluates all 3-stint compound permutations (e.g. S-M-M, M-H-H) to find the optimum 2-stop strategy. | `models/f1_baseline_model.pkl`, `models/encoder.pkl` | None (prints best strategy) |
| `python src/check_name.py` | Prints out all valid driver codes (e.g. VER, HAM, LEC) and circuit names (e.g. Silverstone, Monza) known to the model. | `data/processed/f1_training_data_v2.csv` | None (prints lists) |
| `python src/auto_updater.py` | Checks if a new Grand Prix occurred, downloads official timing data, appends it to `race_data.csv`, and retrains the AI model. | FastF1 API, `data/race_data.csv` | `data/race_data.csv`, `models/*.pkl` |
| `python src/ingest_data.py` | One-time historical ingestion tool that downloads 2023–2025 raw race data from FastF1. | FastF1 API | `data/raw/*` |
| `python src/process_data.py` | Merges individual raw race CSVs into a single clean tabular dataset. | `data/raw/*` | `data/processed/f1_training_data.csv` |
| `python src/add_feature.py` | Adds simulated physical `FuelWeight` (110 kg starting down to 0 kg) based on race progress. | `data/processed/f1_training_data.csv` | `data/processed/f1_training_data_v2.csv` |
| `python src/train_baseline.py` | Trains the HistGradientBoosting machine learning model on historical data. | `data/processed/f1_training_data_v2.csv` | `models/f1_baseline_model.pkl`, `models/encoder.pkl` |

---

## 4. 🖥️ Exploring the Interactive Dashboard (Streamlit App)

Run:
```powershell
python -m streamlit run app.py
```

The application has three core sections accessible via tabs at the top:

### Tab 1: 🏆 Next Race Prediction
- **What it does:** Uses the hardcoded 2026 Formula 1 Calendar (`src/calendar_utils.py`) to automatically detect the next scheduled race based on today's date.
- **Features:**
  - Displays Circuit Name, Country, Date, Round Number, and Total Race Laps.
  - Simulates the entire 2026 driver grid running baseline strategies.
  - Generates a **Predicted Podium** (P1 🥇, P2 🥈, P3 🥉) with predicted race times.
  - Shows an **Expected Finishing Grid** table with detailed gap calculations.

### Tab 2: 🛠️ Strategy Workbench
- **What it does:** Allows you to play the role of Chief Race Strategist for any driver and circuit.
- **Controls in the Left Sidebar:**
  - **Driver:** Choose from all active drivers (e.g., Max Verstappen, Lewis Hamilton, Charles Leclerc).
  - **Circuit:** Choose from all 24 Formula 1 circuits.
  - **Qualifying Scenario:**
    - *Standard (Q3 Top 10):* Normal tyre allocations, used tyre starting set.
    - *Knocked out in Q2 (P11–P15):* Free tyre choice, extra new soft sets saved.
    - *Knocked out in Q1 (P16–P20):* Maximum fresh tyre inventory saved.
  - **Traffic Factor:** Slider from 1.0 (clean air) to 1.5 (heavy DRS trains / midfield traffic).
- **Outputs:**
  - **Recommended Strategy:** Highlights the fastest overall race strategy.
  - **Strategy Battle Table:** Compares 1-stop (e.g. Medium ➔ Hard) vs 2-stop (e.g. Soft ➔ Medium ➔ Hard) strategies with exact pit stop laps, delta times, and stint lengths.
  - **Race Time Delta Chart:** Interactive Altair chart showing time lost relative to the winning strategy.

### Tab 3: 🤖 AI Race Engineer
- **What it does:** A specialized race engineer chatbot powered by Groq's ultra-fast Llama 3.3 (70B) inference engine.
- **Key Capability:** Unlike generic chatbots that guess, this AI has **Function Calling / Tool Execution** enabled. When you ask:
  > *"What is the best strategy for Hamilton at Silverstone if he starts on Hards in heavy traffic?"*
- The AI:
  1. Parses your question into structured parameters (`driver='HAM'`, `circuit='Silverstone'`, `traffic=1.3`, `mode='Standard Q3'`).
  2. Executes the simulation engine in the background (`solve_scenario`).
  3. Formulates a radio-style tactical debrief citing exact lap times, tyre degradation, and pit windows.

---

## 5. 🤖 Setting Up the AI Race Engineer (Groq API Key)

Tab 3 requires an API key from **Groq** (Groq offers a generous **100% free tier** with no credit card required).

### Step 1: Get your free API Key
1. Go to [https://console.groq.com/](https://console.groq.com/).
2. Sign in with Google or GitHub.
3. In the left navigation, click **API Keys**.
4. Click **Create API Key**, give it a name (e.g., `F1-Predictor`), and copy the key (starts with `gsk_...`).

### Step 2: Use the Key (Choose either Method A or Method B)

#### Method A: Enter in the Sidebar (Quickest)
1. Run `python -m streamlit run app.py`.
2. Look at the left sidebar under **"Groq API Key"**.
3. Paste your key into the text box and press Enter.

#### Method B: Save to Secrets (Persistent — No typing needed every launch)
1. Inside the `F1-Predictor` project directory, create a folder named `.streamlit` (if it does not exist).
2. Inside `.streamlit`, create a file named `secrets.toml`.
3. Add the following line:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_groq_api_key_here"
   ```
4. Save the file. The Streamlit app will now automatically log in without prompting you.
*(Note: `.streamlit/secrets.toml` is already listed in `.gitignore` so your key will never be committed to Git).*

---

## 6. 🔬 Full Pipeline from Scratch (Ingestion to Retraining)

If you ever delete the `data/` or `models/` folders, or want to rebuild the entire machine learning engine from the raw official F1 data, run the following steps in sequence:

```
[FastF1 API] 
     │
     ▼ (Step 1: src/ingest_data.py)
[data/raw/ (Season Folders)]
     │
     ▼ (Step 2: src/process_data.py)
[data/processed/f1_training_data.csv]
     │
     ▼ (Step 3: src/add_feature.py)
[data/processed/f1_training_data_v2.csv]
     │
     ▼ (Step 4: src/train_baseline.py)
[models/f1_baseline_model.pkl & encoder.pkl]
     │
     ▼ (Step 5: python -m streamlit run app.py)
[Interactive Dashboard]
```

### Step 1: Ingest Raw Historical Data
```powershell
python src/ingest_data.py
```
- **What happens:** Connects to the official FastF1 timing API and downloads lap times, tyre compounds, tyre age, weather, and race results for the 2023, 2024, and 2025 seasons.
- **Where it saves:** Creates folders inside `data/raw/` (e.g. `data/raw/2024_1_Bahrain/`).
- **Time required:** 10 to 30 minutes depending on your internet connection (data is cached locally in `cache/` so subsequent runs take seconds).

### Step 2: Process and Merge Raw Data
```powershell
python src/process_data.py
```
- **What happens:** Iterates through every race folder in `data/raw/`, cleans out abnormal laps (pit in-laps, red flags), links weather data, and merges everything into one consolidated file.
- **Output:** Saves `data/processed/f1_training_data.csv`.

### Step 3: Add Physics Features (Fuel Load)
```powershell
python src/add_feature.py
```
- **What happens:** F1 cars start with approximately 110 kg of fuel and burn it progressively over the Grand Prix distance. This script calculates the physical fuel weight for every single lap:
  $$\text{FuelWeight} = 110 \times \left(1 - \frac{\text{LapNumber}}{\text{TotalLaps}}\right)$$
- **Output:** Saves `data/processed/f1_training_data_v2.csv`.

### Step 4: Train the Machine Learning Model
```powershell
python src/train_baseline.py
```
- **What happens:**
  1. Loads `data/processed/f1_training_data_v2.csv`.
  2. Encodes categorical variables (`Driver`, `Circuit`, `Compound`) using Scikit-Learn's `OrdinalEncoder`.
  3. Trains a `HistGradientBoostingRegressor` (decision tree ensemble) to learn the exact degradation curves, fuel burn benefits, and circuit characteristics.
  4. Evaluates the Mean Absolute Error (MAE) on unseen validation data (typically ~0.4 to 0.7 seconds per lap).
  5. Serializes and saves the trained brain.
- **Output:**
  - `models/f1_baseline_model.pkl` (Trained model)
  - `models/encoder.pkl` (Categorical feature encoder)

### Step 5: Test the newly trained model
```powershell
python src/predict_lap.py
```
Type in `VER`, `Silverstone`, `SOFT`, `10`, `10`, `no`. If it outputs a lap time around `1:35.xxx` (95.9 seconds), your pipeline is 100% operational!

---

## 7. 🏎️ Running Standalone CLI Simulation Tools

You don't always need to open the web browser. The repository includes high-speed command-line tools for quick analyses:

### 1. Interactive Single Lap Predictor
```powershell
python src/predict_lap.py
```
**Example Session:**
```
--- F1 RACE PREDICTOR (v1) ---
Driver (e.g., VER, HAM): VER
Circuit (e.g., Sakhir, Monza): Silverstone
Tyre Compound (SOFT, MEDIUM, HARD): SOFT
Lap Number (1-70): 10
Tyre Age (Laps driven on these tyres): 10
Is it raining? (yes/no): no

🏁 PREDICTED LAP TIME: 1:35.996
    (Raw Seconds: 95.996s)
```

### 2. Full 57-Lap Race Simulator
```powershell
python src/simulate_race.py
```
Simulates an entire Grand Prix lap-by-lap, displaying tyre degradation degradation and the exact pit stop loss (22.0 seconds) when tyres are changed.

### 3. Fast 1-Stop Pit Window Solver
```powershell
python src/solve_strategy.py
```
Evaluates every single lap between Lap 10 and Lap 45 to find the exact lap that minimizes total race time for a Medium ➔ Hard strategy.

### 4. Brute-Force 2-Stop Strategy Solver
```powershell
python src/solve_2stop.py
```
Uses combinatorial optimization across all tyre combinations (Soft-Medium-Medium, Medium-Hard-Hard, Soft-Hard-Soft, etc.) and evaluates thousands of potential pit stop windows in under 2 seconds.

---

## 8. 🔄 Automated Weekly Updates (GitHub Actions)

This project features an automated MLOps pipeline configured in `.github/workflows/weekly_update.yml`:

- **When it runs:** Automatically every **Monday at 14:00 UTC** (scheduled via CRON).
- **Why Monday at 14:00 UTC?** F1 races take place on Sunday afternoons. FastF1 and official FIA timing telemetry typically require 12 to 24 hours to publish complete, error-free timing logs. The Monday afternoon buffer guarantees clean data availability.
- **What the action executes:**
  1. Spins up a fresh Ubuntu Linux runner.
  2. Installs Python and the required libraries (`pandas`, `scikit-learn`, `joblib`, `fastf1`).
  3. Executes `python src/auto_updater.py`.
  4. Detects the latest completed race of the current season.
  5. Translates official event names to standard circuit names via `CIRCUIT_NAME_MAP`.
  6. Appends the new quicklaps to `data/race_data.csv`.
  7. Retrains the Gradient Boosting model on all historical plus new data.
  8. Commits the updated model (`models/*.pkl`) and dataset (`data/*.csv`) directly back to the GitHub repository.

### Running the Auto-Updater Manually on Your Machine
You can run the exact same auto-updater script anytime:
```powershell
python src/auto_updater.py
```
- If the latest race data is available, it will automatically append the laps and retrain the model.
- If data is not yet available, it will retry 3 times with exponential backoff before safely exiting.

---

## 9. ❓ Troubleshooting & FAQ for Beginners

### Q1: I get `'python' is not recognized as an internal or external command`
- **Cause:** Python is not added to your Windows system PATH.
- **Fix:** Re-run the official Python installer, click **"Modify"**, and check **"Add Python to environment variables"**. Alternatively, use `py` instead of `python`:
  ```powershell
  py -m streamlit run app.py
  ```

### Q2: I get `'pip' is not recognized`
- **Fix:** Always invoke pip through Python directly:
  ```powershell
  python -m pip install -r requirements.txt
  ```

### Q3: Error: `The AI has never seen that Driver, Circuit, or Compound before`
- **Cause:** The machine learning model uses exact naming conventions.
- **Fix:** Check your spelling:
  - **Driver:** Use 3-letter codes in uppercase (`VER`, `HAM`, `LEC`, `NOR`, `PIA`, `RUS`, `SAI`, `ALO`).
  - **Circuit:** Use standard short names (`Silverstone`, `Monza`, `Spa`, `Albert Park`, `Sakhir`, `Suzuka`, `Miami`, `Monaco`, `Zandvoort`, `Hungaroring`).
  - **Tyres:** Must be `SOFT`, `MEDIUM`, or `HARD`.
  - Run `python src/check_name.py` to view the complete list of recognized names.

### Q4: GitHub Actions or Auto-Updater shows `WARNING: Failed to load session info data!` or `DataNotLoadedError`
- **Cause:** FastF1 was queried before the FIA timing servers finalized or uploaded the session telemetry.
- **Fix:** This is **not a code bug**. It is an expected transient state when querying newly concluded sessions. The auto-updater's retry handler will safely exit, and the scheduled Monday CRON job will automatically catch the session once the data is published.

### Q5: Tab 3 (AI Race Engineer) says `Please provide a valid Groq API key`
- **Fix:** Obtain a free key from [console.groq.com](https://console.groq.com/), paste it into the text box in the Streamlit left sidebar, or save it in `.streamlit/secrets.toml` as described in [Section 5](#5--setting-up-the-ai-race-engineer-groq-api-key).

### Q6: Port 8501 is already in use (`Address already in use`)
- **Fix:** Another Streamlit app is already running in the background. Either close that terminal window or specify a different port:
  ```powershell
  python -m streamlit run app.py --server.port 8502
  ```

---
*Happy Racing! If you encounter any unexpected issues, check `localdocs/memory.md` for recent architecture changes and bug fix histories.*
