# 🏎️ F1-Predictor

[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/Samyagya/F1-Predictor)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/AI-Groq%20Llama3-orange?style=for-the-badge)
![FastF1](https://img.shields.io/badge/Data-FastF1-red?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/DevOps-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

**F1-Predictor** is a comprehensive Formula 1 race strategy simulation and prediction tool. It leverages machine learning on historical race data to forecast lap times, determine optimal tyre strategies, and provide an AI-powered race engineer for real-time strategic analysis.

---

## 🚀 Key Features

* **🏆 Next Race Prediction:** Simulates the upcoming Grand Prix for the entire 2026 grid to predict the winner and podium finishers.
* **🛠️ Strategy Workbench:** Run detailed strategy analyses for any driver/circuit combo. Evaluate outcomes based on qualifying results (Q1, Q2, or Q3 elimination).
* **🤖 AI Race Engineer:** An intelligent chatbot powered by **Groq (Llama 3.3)**. Ask natural language questions like *"What is the best strategy for Hamilton at Silverstone if he has no new soft tyres?"* and get data-driven answers.
* **📊 ML-Powered Simulation:** Uses a **Gradient Boosting** model to predict lap times based on tyre compound, age, fuel load, and track conditions.
* **🔄 Automatic Weekly Updates:** A **GitHub Actions** workflow runs every Monday to fetch the latest race data via `fastf1`, automatically retraining the model to keep predictions current.

---

## 🛠️ Tech Stack

**Frontend & Interface**
* **[Streamlit](https://streamlit.io/):** The core web framework used to build the interactive dashboard and chat interface.
* **Pandas:** Used for data manipulation and displaying race statistics tables.

**Artificial Intelligence (The Brain)**
* **[Groq API](https://groq.com/):** High-speed inference engine powering the chat responses.
* **Llama 3.3 (70B Versatile):** The Large Language Model (LLM) that understands natural language queries and executes function calls (strategies).

**Machine Learning & Physics (The Engine)**
* **[FastF1](https://docs.fastf1.dev/):** The library used to ingest real F1 telemetry data (laptimes, tyre degradation, weather).
* **Scikit-Learn:** Used to build the **Gradient Boosting Regressor** that predicts tyre degradation and pit stop loss.
* **Joblib:** Manages model persistence (saving/loading trained models).

**Automation & DevOps**
* **GitHub Actions:** Runs a weekly "CRON job" (every Monday) to fetch new race data, retrain the model, and redeploy the app automatically.
* **Git:** Version control for tracking code and data updates.

---

## 📸 Screenshots

| **AI Race Engineer** | **Strategy Workbench** |
|:---:|:---:|
| ![AI Engineer](image_7e9332.png) | ![Workbench](image_72c1e7.png) |
| *Natural language strategy queries* | *Detailed pit stop analysis* |

---

## ⚙️ How It Works

1. **Data Ingestion:** `src/auto_updater.py` downloads lap-by-lap data from official F1 sessions via `fastf1` and processes it into `data/race_data.csv`.
2. **Model Training:** `src/train_baseline.py` trains a `HistGradientBoostingRegressor` on the processed data to learn relationships between tyre degradation, fuel burn, and pace.
3. **Simulation:** `src/solve_strategy_battle.py` iterates through 1-stop and 2-stop strategies, calculating total race time using the ML model's pace predictions.
4. **AI Agent:** `src/llm_agent.py` initializes a Groq Llama 3 agent. It translates user questions into simulation parameters, runs the simulation tool, and explains the results in plain English.
5. **Interface:** `app.py` ties everything together into a Streamlit dashboard.

---

## 🏃‍♂️ How to Run

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/samyagya/F1-Predictor.git]
   cd F1-Predictor
