# Rules — F1 2026 Strategy Oracle

These are the coding standards, library choices, and AI boundaries for this project.

---

## 1. Libraries to USE

### Core Stack (Non-negotiable)
| Library | Why |
|---|---|
| `streamlit` | Only web framework. Do not add Flask, FastAPI, or Dash. |
| `pandas` | All tabular data manipulation. Use DataFrames, not raw dicts where possible. |
| `joblib` | Model save/load only. Use joblib.dump() and joblib.load(). |
| `scikit-learn` | ML model training and encoding. Stick to GradientBoostingRegressor or HistGradientBoostingRegressor. |
| `groq` | LLM inference. Use the official Groq Python SDK. |
| `fastf1` | Data ingestion only (in auto_updater.py and ingest_data.py). Never import fastf1 in app.py. |

### Allowed Supporting Libraries
| Library | Use Case |
|---|---|
| `os`, `sys` | File path management and module path fixes |
| `json` | Tool call argument parsing in llm_agent.py |
| `datetime` | Date comparisons for calendar_utils.py |
| `re` | Regex NLU in ai_analyst.py |
| `random` | Personality response rotation |
| `itertools` | Compound permutations in solve_2stop.py |
| `glob`, `shutil` | Batch file operations in ingest_data.py and process_data.py |

---

## 2. Libraries to AVOID

| Library | Reason to Avoid |
|---|---|
| `matplotlib` / `seaborn` | Only in visualize.py (offline script). Do NOT add to Streamlit app; use Streamlit native charts or Altair. |
| `tensorflow` / `pytorch` | Overkill for tabular data. The GradientBoosting model is sufficient. |
| `openai` | We use Groq. Do not switch LLM providers without updating secrets management. |
| `flask` / `fastapi` | Streamlit handles routing. No REST API layer needed. |
| `sqlalchemy` / `sqlite` | Data lives in CSV files. No database layer. |
| `numpy` (direct) | Only use numpy if scikit-learn requires it indirectly. Prefer pandas operations. |
| `tqdm` | Only in offline process_data.py. Do not use in Streamlit (use st.progress() instead). |

---

## 3. Code Style Rules

- **All paths must use `os.path.join()`** — never hardcode backslash paths.
- **Model loading**: Always check `os.path.exists()` before loading .pkl files and raise a clear FileNotFoundError.
- **Streamlit state**: Use `st.session_state` for all persistent state (chat history, agent instance).
- **Error handling**: Wrap all ML predictions and API calls in try/except. Surface errors with `st.error()` in the UI.
- **No print() in app.py**: Use st.write(), st.error(), st.success(), or st.caption() for all user-facing output.
- **Feature order**: The model expects features in this exact order: `['Driver', 'Circuit', 'Compound', 'TyreLife', 'LapNumber', 'Rainfall', 'FuelWeight']`. Never change this without retraining the model AND encoder.

---

## 4. AI / LLM Boundaries

### What the LLM CAN do:
- Interpret natural language strategy questions
- Call the `run_strategy_simulation` tool to get simulation results
- Explain simulation results in plain English
- Refuse to answer if it cannot identify a valid driver or circuit
- Respond to greetings and general F1 knowledge questions from memory

### What the LLM CANNOT do:
- Make up or hallucinate race times — it MUST call the tool for any numeric strategy answer
- Access the internet, live F1 timing, or real-time telemetry
- Know about races that happened after its training cutoff
- Modify the ML model or training data
- Execute arbitrary Python code on the server

### LLM Architecture Rules:
- Always use `tool_choice="auto"` — never force a tool call for general questions
- The system prompt must include: "Do not guess. Run the simulation."
- Never pass user input directly to the shell or file system
- The `constraints_description` field in the tool is plain English — parse it in Python, not in the LLM prompt

---

## 5. Data Rules

- `data/race_data.csv` is the single source of truth for training data
- Never delete or overwrite race_data.csv manually; only append via auto_updater.py
- Rainfall column must always be binary (0 = dry, 1 = wet). Never use True/False strings.
- FuelWeight must be calculated as: `max(0, 110 - (LapNumber * 1.7))`
- All LapTime values must be in seconds (float), never as timedelta strings

---

## 6. DevOps Rules

- The weekly_update.yml workflow must always write back to the same branch (main)
- Model files (.pkl) and data files (.csv) must be committed together in one atomic commit
- Never store the Groq API key in code or .env files — use Streamlit Secrets (st.secrets) or the sidebar input
- The `cache/` directory (FastF1 cache) must be gitignored and never committed
