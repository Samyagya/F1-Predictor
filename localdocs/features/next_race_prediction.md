# Feature: Next Race Prediction

---

## What This Feature Does

The Next Race Prediction tab (Tab 1 in app.py) is the headline feature of the app. When the user clicks "Predict Race Winner", it:

1. Reads the current date and finds the next upcoming Grand Prix from the 2026 race calendar
2. Simulates the **full 22-driver grid** — running the strategy engine for every driver
3. Applies driver-tier skill biases to account for pace differences the ML model cannot capture
4. Sorts all drivers by projected race time and displays:
   - A three-column podium widget (P1 centre, P2 left, P3 right)
   - A full 22-driver race classification table with gaps to the leader
   - A real-time Streamlit progress bar as each driver is simulated

---

## Files Involved

| File | Role |
|---|---|
| `app.py` (Tab 1 block, lines 85-139) | UI rendering, driver loop, bias application |
| `src/calendar_utils.py` | Provides `get_next_race()` — returns circuit name + date |
| `src/solve_strategy_battle.py` | Provides `solve_scenario()` — returns best strategy + race time |
| `src/physics.py` | Provides `get_pit_loss()` — circuit-specific pit lane loss in seconds |

---

## Tech Stack

| Component | Technology |
|---|---|
| UI Framework | Streamlit (st.progress, st.metric, st.dataframe, st.columns) |
| Data Manipulation | Pandas (DataFrame for final table display) |
| Strategy Engine | solve_strategy_battle.py (GradientBoosting model + physics) |
| Calendar | Hardcoded Python dict list in calendar_utils.py |

---

## How It Works (Step by Step)

1. `get_next_race()` scans the RACE_CALENDAR list and returns the first race whose date is >= today (mapped to 2026)
2. `run_scenario_analysis(driver_code, circuit, "Standard Q3")` is called for each of the 22 drivers
3. Inside that function:
   - `load_artifacts()` loads the .pkl model and encoder
   - `get_pit_loss(circuit)` returns the circuit-specific pit stop time loss
   - `solve_scenario()` evaluates 6 compound strategy templates and returns the fastest one
4. A driver-tier bias is applied:
   - Top drivers (VER, HAM, LEC, NOR): -5 seconds
   - Back markers (BOT, HUL, OCO): +10 seconds
5. All results are sorted by final time
6. Gap to leader is computed for each driver
7. Results are rendered in the podium layout + full table

---

## Decisions Made for This Feature

### Why hardcode the 22-driver grid in app.py?
The 2026 F1 grid includes several new teams (Audi, Cadillac) and driver movements. FastF1 does not yet have complete 2026 roster data, so the grid is hardcoded in both `app.py` and `src/ai_analyst.py` as a Python dict: `{"Driver Full Name (Team)": "3-LETTER-CODE"}`.

### Why use "Standard Q3" as the only mode for race prediction?
The full race prediction is a simplification — we assume all 22 drivers qualified and used softs in Q3 (the most common real-world scenario for a top-order grid). The Workbench tab allows per-driver qualifying mode customisation.

### Why not simulate lap-by-lap?
A full lap-by-lap simulation for 22 drivers at ~57 laps each would be 1,254 ML predictions. Using the stint-average approximation in `solve_strategy_battle.py`, only ~6 predictions per driver are needed (one per strategy template), making the full grid simulation finish in under 30 seconds.

### Why apply hardcoded driver skill bias?
The ML model predicts lap pace from tyre compound, age, fuel, and circuit — not from driver identity (even though Driver is a feature, the model generalises poorly to new drivers). The bias approximates the real-world performance gap: a ~0.5-1s/lap pace delta over a race distance (~57 laps) translates to roughly 5-10 seconds total, matching the chosen bias values.

### Why display P2 on the left and P1 in the centre?
This mirrors the physical podium layout used in F1 (highest step in the middle). It creates a visual hierarchy that makes P1 feel earned.
