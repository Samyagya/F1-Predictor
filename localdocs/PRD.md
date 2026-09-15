# Product Requirements Document — F1 2026 Strategy Oracle

---

## 1. Product Overview

**F1 2026 Strategy Oracle** is a Formula 1 race strategy simulation and prediction web application. It uses historical race telemetry data, machine learning models, and a large language model (LLM) AI agent to:

- Predict race winners and podium finishers for upcoming Grand Prix events
- Compute optimal pit stop strategies for any driver at any circuit
- Allow users to converse naturally with an AI race engineer that runs real simulations

The app is built with a "data flywheel" design: every Monday after a race weekend, a GitHub Actions automation pipeline fetches new data via FastF1, retrains the ML model, and pushes updated artifacts to the repository, keeping predictions continuously improving.

---

## 2. Target Users

| User Type | Profile | Primary Use |
|---|---|---|
| **F1 Fans** | Enthusiasts who watch races and want data-backed insights | Check race predictions, explore strategies for their favourite driver |
| **Fantasy F1 Players** | Players in F1 Fantasy who need strategy intel | Understand which drivers have tyre advantages and optimal strategies |
| **Data Science Learners** | Students exploring ML + sports analytics | Study how gradient boosting, feature engineering, and NLP combine |
| **Casual Curious Visitors** | People who stumble on the app before a race weekend | Quick race winner prediction with minimal input |

---

## 3. Core Problem Being Solved

F1 strategy is one of the most complex real-time decision problems in sport. For fans, understanding why a team pits early or which compound to start on is opaque. This app democratises that insight making it interactive, explainable, and available without needing a team of engineers.

---

## 4. Features

### 4.1 Next Race Prediction (Tab 1)
- Automatically detects the next upcoming Grand Prix from the hardcoded 2026 calendar
- Simulates the **full 22-driver grid** to produce a predicted finishing order
- Applies driver-skill biases (top drivers like Verstappen, Hamilton, Norris get -5s; lower-midfield get +10s)
- Displays podium (P1, P2, P3) with gaps and a full race classification table
- Uses a Streamlit progress bar while simulating

### 4.2 Strategy Workbench (Tab 2)
- User selects any driver + any circuit from dropdowns
- Simulates **3 scenario modes** based on qualifying elimination round:
  - Q3 (P1-P10): Used softs, limited tyre inventory
  - Q2 (P11-P15): Some fresh softs available
  - Q1 (P16-P20): Full fresh softs, most strategic freedom
- Evaluates 6 strategy templates (1-stop and 2-stop combinations) and returns the fastest
- Displays strategy type, stint breakdown, and total projected race time

### 4.3 AI Race Engineer (Tab 3)
- Groq-powered chatbot using Llama 3.3 70B
- Users ask natural language questions e.g. "What is Hamilton's best strategy at Silverstone with no new softs?"
- AI decides when to call the simulation tool vs. answer directly
- Two-turn architecture: LLM -> Tool Call -> Final LLM Answer
- Persistent chat history within the session
- Requires Groq API key (from Streamlit secrets or sidebar input)

### 4.4 Automatic Weekly Model Update (CI/CD)
- GitHub Actions workflow triggers every Monday at 14:00 UTC
- Fetches latest race session data via FastF1 with retry logic (3 attempts)
- Appends new lap data to data/race_data.csv
- Retrains a GradientBoostingRegressor model
- Auto-commits models/*.pkl and data/*.csv back to the repository

---

## 5. Non-Goals (Out of Scope)

- Real-time live lap-by-lap tracking during an active race
- Weather-adaptive strategy (currently assumes dry conditions)
- Qualifying lap time predictions (only race pace modelled)
- Official F1 data feeds (uses FastF1 which accesses cached public data)
- Multi-season historical leaderboards or driver stats pages

---

## 6. Success Metrics

- App loads and simulates a full race grid in under 30 seconds
- AI chatbot returns a coherent, simulation-backed answer in under 10 seconds
- Model retraining succeeds weekly without manual intervention
- Mean Absolute Error (MAE) of the lap time model below 2.0 seconds
