# Memory — F1 2026 Strategy Oracle

This file tracks what has been built, what is in progress, key decisions made, and why they were made.
Update this file every time a significant change is made.

---

## Current Status (as of 2026-09-15)

**Overall Phase:** All 8 bugs fixed and verified. Project is in a stable, correct state.
**Active File:** None — all bug fixes complete.

---

## What Has Been Completed

### Files Completed / Modified
| File | Status | Notes |
|---|---|---|
| `app.py` | DONE (bug fixed) | Bug #6: agent now re-inits when API key changes |
| `src/physics.py` | DONE (bug fixed) | Bug #5: Imola pit loss added (23.0s) |
| `src/calendar_utils.py` | DONE | 2026 hardcoded calendar with 24 rounds |
| `src/solve_strategy_battle.py` | DONE (3 bugs fixed) | Bug #2: mode now drives tyre inventory; Bug #3: traffic now flows to get_stint_time; Bug #7: dead `strategies=[]` removed |
| `src/llm_agent.py` | DONE (bug fixed) | Bug #4: `desc` variable renamed to `constraint_text` |
| `src/auto_updater.py` | DONE (2 bugs fixed) | Bug #1: CIRCUIT_NAME_MAP added; Bug #8: dead LabelEncoder import removed |
| `src/ai_analyst.py` | DONE (legacy) | Earlier regex-based NLU. Not used in production app. |
| `src/ingest_data.py` | DONE | One-time bulk ingestion 2023-2025 |
| `src/process_data.py` | DONE | Merges raw CSVs into flat training file |
| `src/add_feature.py` | DONE | Adds FuelWeight feature to dataset |
| `src/train_baseline.py` | DONE | Offline model training script |
| `src/predict_lap.py` | DONE | CLI lap time predictor |
| `src/simulate_race.py` | DONE | CLI lap-by-lap race simulator |
| `src/solve_strategy.py` | DONE | CLI 1-stop pit window finder |
| `src/solve_2stop.py` | DONE | CLI brute-force 2-stop optimiser |
| `src/tyre_strategy.py` | DONE | Tyre inventory after qualifying modes |
| `src/visualize.py` | DONE | Generates tyre degradation PNG |
| `src/check_name.py` | DONE | CLI utility for valid driver/circuit names |
| `.github/workflows/weekly_update.yml` | DONE | Monday 14:00 UTC CRON automation |
| `models/f1_baseline_model.pkl` | DONE (retrained) | Retrained on corrected circuit-name data |
| `models/encoder.pkl` | DONE (retrained) | Retrained on corrected circuit-name data |
| `data/race_data.csv` | DONE (normalised) | All 6399 rows updated with short circuit names |
| `localdocs/guide.md` | DONE | Comprehensive zero-knowledge user guide created |
| `localdocs/` | DONE | Full documentation suite created and updated |

---

## Bug Fixes Applied (2026-09-15)

### Bug #1 — CRITICAL: Circuit Name Mismatch
**Problem:** `auto_updater.py` stored circuit names as FastF1 EventName strings (e.g. "British Grand Prix"). The app passes short names at inference (e.g. "Silverstone"). The encoder was trained on full names, so every inference call resulted in unknown-value encoding (-1) for circuit. All circuit-specific pace differences were silently wrong.
**Fix:** Added `CIRCUIT_NAME_MAP` dict to `auto_updater.py` that translates full event names to short names at ingestion time. Normalised existing `data/race_data.csv` (all 6399 rows). Retrained model and encoder on corrected data.
**Verification:** Model predicts VER at Silverstone SOFT as 1m 35.996s (95.9s) — correct F1 race lap range.

### Bug #2 — CRITICAL: Mode Parameter Unused
**Problem:** `solve_scenario()` accepted `mode` ("Standard Q3", "Knocked out in Q2", "Knocked out in Q1") but never read it. All 3 Strategy Workbench scenarios returned the same result.
**Fix:** `solve_scenario()` now calls `get_race_start_tyres(driver_code, mode)` from `tyre_strategy.py` to build the tyre inventory. Strategy templates are filtered to only include those where (a) the starting compound has a NEW set available, and (b) all other compounds exist in inventory.

### Bug #3 — HIGH: Traffic Factor Not Applied
**Problem:** `traffic` parameter was received by `solve_scenario()` but never forwarded to `get_stint_time()`, which always used its default `traffic_factor=1.0`.
**Fix:** `get_stint_time()` is now called with `traffic_factor=traffic` in `solve_scenario()`.
**Verification:** traffic=1.5 produces ~135m vs traffic=1.0 at ~90m — the 1.5x multiplier is now active.

### Bug #4 — HIGH: Variable Shadowing in llm_agent.py
**Problem:** `desc = constraints_description.lower()` on line 31 was overwritten by `strat, desc, time = solve_scenario(...)` on line 42. The variable name collision was confusing and error-prone.
**Fix:** Renamed the constraint parsing variable to `constraint_text`.

### Bug #5 — MEDIUM: Imola Missing from Pit Loss Table
**Problem:** Imola (Round 7 in the 2026 calendar) was missing from `physics.py`, causing it to fall back to the wrong default of 22.5s.
**Fix:** Added `'Imola': 23.0` to the lookup table.

### Bug #6 — MEDIUM: Agent Not Re-initialised on API Key Change
**Problem:** If a user typed a wrong API key and then corrected it, the stale agent (or non-existent one) persisted because the check was only `if "agent" not in st.session_state`.
**Fix:** Added `st.session_state.last_api_key` tracking. The agent is reinitialised whenever `api_key != st.session_state.last_api_key`.

### Bug #7 — LOW: Dead `strategies = []` Variable
**Problem:** An empty `strategies = []` list was initialised in `solve_scenario()` but never appended to or returned — purely dead code.
**Fix:** Removed the dead line.

### Bug #8 — LOW: Unused LabelEncoder Import
**Problem:** `auto_updater.py` imported `LabelEncoder` from sklearn but only used `OrdinalEncoder`. Dead import.
**Fix:** Removed the import.

---

## Key Decisions Made

### 1. Streamlit as the only framework
**Decision:** Use Streamlit, no Flask, no React.
**Why:** The app is Python-native, data-heavy, and needs rapid iteration. Streamlit handles state, UI components, and hosting out of the box.

### 2. Groq over OpenAI
**Decision:** Use Groq API with Llama 3.3 70B, not OpenAI GPT-4.
**Why:** Groq is ~10x faster at inference, has a generous free tier, and Llama 3.3 70B supports function calling natively.

### 3. GradientBoostingRegressor over Neural Networks
**Decision:** Use scikit-learn GradientBoosting, not deep learning.
**Why:** Tabular regression on 7 structured features does not benefit from neural networks. Gradient boosting trains fast and achieves low MAE.

### 4. OrdinalEncoder over OneHotEncoder
**Decision:** Encode Driver, Circuit, Compound with OrdinalEncoder.
**Why:** 22 drivers + 22 circuits + 5 compounds with OneHot would create ~50 extra columns. OrdinalEncoder keeps the feature space compact.

### 5. Stint-average approximation in solve_strategy_battle.py
**Decision:** Predict pace for the average lap of a stint rather than per-lap.
**Why:** Full grid simulation (6 strategies x 22 drivers) would be too slow lap-by-lap.

### 6. Hardcoded 2026 race calendar in calendar_utils.py
**Decision:** Calendar is a hardcoded Python list.
**Why:** FastF1 may not have complete 2026 calendar data. Hardcoding guarantees reliability.

### 7. Driver skill bias in race prediction
**Decision:** Apply hardcoded time bias based on driver tier.
**Why:** The ML model predicts lap times from tyre/fuel physics, not driver skill. Bias approximates the real performance gap.

### 8. Two-turn LLM architecture in llm_agent.py
**Decision:** Two separate Groq API calls — first for tool intent, second for final answer.
**Why:** Required by the Groq function calling pattern — tool results must be added to history before the final completion call.

### 9. CIRCUIT_NAME_MAP in auto_updater.py (Bug #1 fix decision)
**Decision:** Map FastF1 EventName to short circuit names at ingestion time, not at inference time.
**Why:** Fixing at ingestion is the single source of truth. If fixed at inference, every predict call would need its own mapping, duplicating logic across solve_strategy_battle.py, llm_agent.py, and app.py.

### 10. Tyre inventory filtering for mode parameter (Bug #2 fix decision)
**Decision:** Filter strategy templates using the inventory from `tyre_strategy.get_race_start_tyres()` rather than hardcoding per-mode lists.
**Why:** `tyre_strategy.py` already contains the correct inventory logic for each qualifying mode. Reusing it avoids duplicating that logic and keeps the tyre management rule in one place.

---

## Known Remaining Issues / Future Work

| Issue | Severity | Notes |
|---|---|---|
| Total laps hardcoded to 57 | Medium | All circuits assumed 57 laps. Should be a per-circuit lookup. |
| Driver skill bias is arbitrary | Medium | +/-5s/10s values are estimates, not data-driven. |
| Rainfall hardcoded to 0 at prediction | Low | Strategy always assumes dry. |
| Monaco/Imola/etc not in training data | Medium | Only 7 circuits are in the current race_data.csv (2026 races so far). Strategy for circuits not in training data uses OrdinalEncoder unknown value (-1). Will fix itself as more races are run and auto_updater adds their data. |
| Q3/Q1 strategy difference is minor | Low | Because all compound types are in every inventory (SOFT, MEDIUM, HARD), the only filtering effect is on starting compound being NEW. With more granular inventory tracking this could be more differentiated. |
