# Feature: Physics Engine

---

## What This Feature Does

The Physics Engine (`src/physics.py`) provides two core capabilities that the ML model alone cannot offer:

1. **Pit Lane Time Loss** — A lookup table of the exact time (in seconds) lost during a pit stop at each F1 circuit. This is critical for comparing 1-stop vs 2-stop strategies because a 2-stop has twice the pit loss.

2. **Tyre Cliff Penalty** — A mathematical formula that models the rapid lap time degradation that occurs when a tyre is pushed beyond its designed life window ("the cliff").

These two functions are used by `solve_strategy_battle.py` to produce physically accurate race time estimates.

---

## Files Involved

| File | Role |
|---|---|
| `src/physics.py` | The only file — contains both functions |
| `src/solve_strategy_battle.py` | Calls `get_pit_loss()` for every strategy evaluation |
| `src/llm_agent.py` | Calls `get_pit_loss()` via the tool function |
| `src/ai_analyst.py` | Calls `get_pit_loss()` for inline pit loss queries |

---

## Tech Stack

| Component | Technology |
|---|---|
| Implementation | Pure Python — no external libraries |
| Data Source | Hand-researched F1 pit lane delta times (2024-2026 seasons) |

---

## Function 1: get_pit_loss(circuit)

Returns the time in seconds lost during a pit stop at the given circuit.

Pit loss varies by circuit because:
- Pit lane length varies (Monaco has the shortest pit lane in F1)
- Speed limits in pit lane are standardised (80 km/h) but total distance differs
- Entry and exit geometry affects total delta time

### Circuit Data (22 circuits covered)

| Category | Circuits | Loss (seconds) |
|---|---|---|
| High pit loss (>24s) | Silverstone, Singapore, Paul Ricard, Lusail, Suzuka | 25-29s |
| Medium pit loss (22-24s) | Sakhir, Shanghai, Miami, Barcelona, Monza, Las Vegas, Yas Marina | 22-24s |
| Low pit loss (<22s) | Spa, Red Bull Ring, Baku, Interlagos, Montreal, Monaco | 19-21s |

**Default:** 22.5 seconds for any unknown circuit.

---

## Function 2: calculate_tyre_cliff_penalty(compound, age)

Returns additional seconds added to a lap time when a tyre exceeds its designed life window.

### Compound Life Windows

| Compound | Max Life (Laps) | Cliff Steepness |
|---|---|---|
| SOFT | 15 laps | 0.35s per lap^2 |
| MEDIUM | 20 laps | 0.35s per lap^2 |
| HARD | 25 laps | 0.35s per lap^2 |
| INTERMEDIATE | 28 laps | 0.35s per lap^2 |
| WET | 28 laps | 0.35s per lap^2 |

### Formula
```
if age > limit:
    over_limit = age - limit
    penalty = 0.35 * (over_limit ** 2)
```

This models the exponential degradation where tyres don't just slow down linearly — they fall off a "cliff" rapidly once past their designed operating window.

**Note:** `calculate_tyre_cliff_penalty()` is defined in physics.py but is NOT currently called by `solve_strategy_battle.py`. It was developed for a future version that will do per-lap simulation instead of stint averaging. It is preserved for Phase 7.

---

## Decisions Made for This Feature

### Why a lookup table for pit loss instead of computing it?
Pit lane length and geometry is track-specific and does not change race to race. A lookup table is the most accurate approach — the values were calibrated against observed F1 pit stop delta times from 2024 season data. Computing it from first principles (speed limit × distance) would require geometry data not available in FastF1.

### Why 22.5 seconds as the default for unknown circuits?
22.5 seconds is the average pit loss across the known circuits in the lookup table. It provides a reasonable fallback when a new circuit is added to the calendar before its pit loss is measured and added.

### Why is the Hard tyre cliff at 25 laps, not the previous 35?
The comment in the code says "NERFED: Was 35. Now dies at 25." This reflects real-world observations where F1 hard tyres in recent seasons have degraded faster than teams anticipated, partly due to higher-downforce cars generating more heat. The 25-lap limit better matches the 2024-2026 tyre behaviour.

### Why is the cliff penalty quadratic (^2) rather than linear?
Real tyre degradation data shows an exponential cliff, not a linear one. The quadratic formula `0.35 * (over_limit^2)` creates a steep but controlled curve: 1 lap over = 0.35s, 2 laps over = 1.4s, 3 laps over = 3.15s. This matches the "sudden death" behaviour observed when teams push tyres too long.

### Why is calculate_tyre_cliff_penalty not used in the current production solver?
The current strategy engine uses a stint-average approximation for speed. Adding per-lap cliff penalties would require per-lap simulation (57 model calls instead of 1 per stint). This is reserved for a future high-fidelity simulation mode where accuracy is prioritised over speed.
