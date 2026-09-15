# Feature: Automatic Weekly Model Update

---

## What This Feature Does

The auto-updater is a fully automated CI/CD pipeline that runs every Monday at 14:00 UTC (approximately 22-23 hours after a Sunday race). It:

1. Detects the most recently completed F1 race using FastF1
2. Checks if that race's data is already in the dataset (idempotent)
3. Downloads lap-by-lap data from the race session via FastF1
4. Appends the new data to `data/race_data.csv`
5. Retrains the GradientBoostingRegressor on the updated dataset
6. Saves the new `models/f1_baseline_model.pkl` and `models/encoder.pkl`
7. Auto-commits and pushes all changed files back to the repository

This creates a self-improving "data flywheel" — the more races that happen, the better the model becomes, automatically.

---

## Files Involved

| File | Role |
|---|---|
| `src/auto_updater.py` | Main script: fetch, process, retrain, save |
| `.github/workflows/weekly_update.yml` | GitHub Actions CRON trigger and runner |
| `data/race_data.csv` | Dataset that gets appended to each week |
| `models/f1_baseline_model.pkl` | Model file that gets overwritten with new version |
| `models/encoder.pkl` | Encoder file that gets overwritten with new version |

---

## Tech Stack

| Component | Technology |
|---|---|
| CI/CD Runner | GitHub Actions (ubuntu-latest) |
| Schedule Trigger | CRON expression: `0 14 * * 1` (Monday 14:00 UTC) |
| F1 Data Source | FastF1 Python library (official F1 data) |
| Model | scikit-learn GradientBoostingRegressor |
| Encoder | scikit-learn OrdinalEncoder |
| Persistence | joblib.dump() / joblib.load() |
| Git Automation | stefanzweifel/git-auto-commit-action@v5 |

---

## GitHub Actions Workflow

```yaml
Trigger: Every Monday 14:00 UTC + manual dispatch
Runner: ubuntu-latest

Steps:
1. Checkout repository
2. Set up Python 3.9
3. pip install pandas scikit-learn joblib fastf1
4. python src/auto_updater.py
5. git-auto-commit: commit models/*.pkl + data/*.csv
```

---

## Retry Logic

FastF1 data can take time to become available after a race. The updater implements:
- **3 retry attempts** with a **60-second delay** between attempts
- If all 3 attempts fail, the workflow marks the run as FAILED (visible in GitHub Actions UI)
- If data is not yet available, the race will be picked up on the next Monday run

---

## Decisions Made for This Feature

### Why run on Monday instead of Sunday night?
Race data via FastF1 typically takes 12-24 hours to be processed and published. Running on Monday at 14:00 UTC gives a ~22-hour buffer after a typical Sunday 14:00 UTC race end time.

### Why use `pick_quicklaps()` to filter laps?
FastF1's `pick_quicklaps()` removes outlier laps (in-laps, out-laps, safety car laps, laps after red flags). Training on clean racing laps produces a more accurate pace model than raw all-laps data.

### Why retrain from scratch on every update instead of incremental learning?
Gradient Boosting does not support incremental (online) learning in scikit-learn. A full retrain is required. This is fast enough (~30-60 seconds) given the dataset size and the weekly frequency.

### Why use OrdinalEncoder with `handle_unknown='use_encoded_value', unknown_value=-1`?
New drivers or circuits that appear in 2026 but were not in the 2023-2025 training data would cause an error with a strict encoder. Setting unknown_value=-1 allows the model to make a prediction (possibly less accurate) for unseen categories rather than crashing.

### Why commit .pkl files to git?
The Streamlit app loads models at runtime from the local filesystem. The simplest way to make updated models available to the deployed Streamlit Cloud app is to commit them to the repository. Streamlit Cloud redeploys automatically on new commits.

### Why use manual_dispatch in addition to the CRON schedule?
`workflow_dispatch` allows a developer to manually trigger the pipeline via the GitHub Actions UI. This is useful for testing after a major race (e.g., season opener) or for re-running a failed weekly job without waiting until next Monday.
