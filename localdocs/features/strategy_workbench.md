# Feature: Strategy Workbench

---

## What This Feature Does

The Strategy Workbench (Tab 2 in app.py) is the analytical power tool of the app. It lets the user:

1. Select any driver from the full 2026 grid
2. Select any circuit from the 22-race calendar
3. Simulate all 3 qualifying elimination scenarios to understand how starting grid position affects optimal strategy

For each of the 3 qualifying modes, the workbench runs the strategy engine and displays:
- The recommended strategy (e.g. "2 Stop (SOFT -> MEDIUM -> SOFT)")
- A description of the stint breakdown
- The projected total race time as a st.metric widget

---

## Files Involved

| File | Role |
|---|---|
| `app.py` (Tab 2 block, lines 144-172) | UI layout, dropdowns, scenario loop |
| `src/solve_strategy_battle.py` | `solve_scenario()` — strategy evaluation engine |
| `src/tyre_strategy.py` | `get_race_start_tyres()` — models tyre inventory after qualifying |
| `src/physics.py` | `get_pit_loss()` — pit lane time loss per circuit |

---

## Tech Stack

| Component | Technology |
|---|---|
| UI Framework | Streamlit (st.selectbox, st.spinner, st.success, st.metric, st.container) |
| Strategy Evaluation | solve_strategy_battle.py with GradientBoosting model |
| Tyre Inventory Modelling | tyre_strategy.py (pure Python, no ML) |
| Physics Constants | physics.py pit loss lookup table |

---

## The 3 Qualifying Scenarios

### Standard Q3 (P1–P10)
- Driver made it through Q1, Q2, and Q3
- Used 2 soft sets in Q1+Q2, plus 2 more in Q3 (4 softs used total)
- Only 0 new soft sets remaining for the race
- Forces a strategy with used softs or switches to medium/hard-led strategy

### Knocked out in Q2 (P11–P15)
- Driver used 2 soft sets (Q1 + Q2 attempt) before elimination
- 2 fresh (new) soft sets remain
- More strategic flexibility — can start on fresh softs

### Knocked out in Q1 (P16–P20)
- Only 1 soft set used before elimination
- 3 fresh soft sets remain
- Maximum tyre freedom — can run an aggressive multi-stop on fresh softs

---

## Strategy Templates Evaluated

All 3 scenarios run the same 6 strategy templates through `solve_scenario()`:

1. SOFT -> MEDIUM (1-stop)
2. MEDIUM -> HARD (1-stop)
3. SOFT -> HARD (1-stop)
4. SOFT -> MEDIUM -> SOFT (2-stop Aggressive)
5. SOFT -> MEDIUM -> MEDIUM (2-stop Balanced)
6. MEDIUM -> HARD -> MEDIUM (2-stop Conservative)

The winner is whichever template produces the minimum total race time.

---

## Decisions Made for This Feature

### Why simulate 3 qualifying scenarios instead of letting the user choose a grid position?
Qualifying position is the key strategic variable for the race — it determines which tyres were used in qualifying and therefore what inventory is available on Sunday. Presenting 3 pre-defined scenarios (Q3 / Q2 / Q1) covers the most meaningful strategic decision points without overwhelming the user with a full 20-position selector.

### Why use st.spinner() instead of st.progress() for the workbench?
The workbench simulates 3 scenarios sequentially, not 22 drivers. Each scenario runs in approximately 1-3 seconds. A spinner ("Simulating...") is appropriate for short blocking operations. A progress bar is reserved for the longer 22-driver race simulation in Tab 1.

### Why show all 3 scenarios simultaneously rather than one at a time?
Showing all 3 scenarios in a single view lets the user immediately compare the strategic impact of qualifying position. This is the core analytical value of the workbench — "if Norris qualifies P3 vs. P12, which strategy changes?"

### Why use st.container() + st.divider() to separate scenarios?
Each scenario is visually isolated with a divider to prevent the report from looking like one wall of text. The container ensures the layout is controlled even if Streamlit rerenders.

### Why not persist workbench results between sessions?
Strategy results are circuit + driver specific and should always be freshly simulated. There is no user account system, so caching results between sessions would require a database (out of scope).
