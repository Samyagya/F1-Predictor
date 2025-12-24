import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- IMPORT BACKEND ---
try:
    from src.physics import get_pit_loss
    from src.solve_strategy_battle import solve_scenario, load_artifacts
    from src.calendar_utils import get_next_race 
    from src.llm_agent import F1Agent
except ImportError:
    st.error("Could not import 'src'.")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="F1 2026 Oracle", page_icon="🏎️", layout="wide")

# --- SECRETS MANAGEMENT (The Fix) ---
# Check if key is in Secrets (Cloud/Local), otherwise ask user
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Fallback for manual entry if secret is missing
    with st.sidebar:
        st.warning("⚠️ No Main API Key found.")
        api_key = st.text_input("Enter Gemini API Key", type="password")

# --- INITIALIZE CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Radio check. I am connected to the simulation engine. What's the plan?"}
    ]

# Initialize Agent if key exists
if "agent" not in st.session_state and api_key:
    st.session_state.agent = F1Agent(api_key)

# --- TABS ---
st.title("🏎️ F1 2026 Strategy Oracle")
tab1, tab2, tab3 = st.tabs(["🔮 Next Race", "🛠️ Workbench", "💬 AI Engineer"])

# =========================================================
# TAB 1: NEXT RACE PREDICTOR (Standard Logic)
# =========================================================
# (Include your previous TAB 1 code here. I'm keeping it brief for the solution)
with tab1:
    st.header("Next Grand Prix Predictor")
    # ... (Your existing Tab 1 code) ...
    # Placeholder for brevity:
    next_race = get_next_race()
    st.caption(f"Next Race: {next_race['circuit']}")
    if st.button("Predict Winner"):
        st.info("Simulating... (Add your previous Tab 1 logic here)")

# =========================================================
# TAB 2: STRATEGY WORKBENCH (Standard Logic)
# =========================================================
# (Include your previous TAB 2 code here)
with tab2:
    st.header("Strategy Workbench")
    # ... (Your existing Tab 2 code) ...

# =========================================================
# TAB 3: AI RACE ENGINEER (LLM POWERED)
# =========================================================
with tab3:
    st.header("💬 Intelligent Pit Wall")
    
    if not api_key:
        st.info("Please configure the API Key to use the chatbot.")
    else:
        # 1. Display Chat
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 2. Input
        if prompt := st.chat_input("Ask anything: 'Strategy for Max if he has no softs?'"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # Use status container for "thinking" effect
                with st.status("🧠 Thinking & Simulating...", expanded=True) as status:
                    if "agent" in st.session_state:
                        response_text = st.session_state.agent.ask(prompt)
                        status.update(label="Transmission Received", state="complete", expanded=False)
                    else:
                        response_text = "Connection Error: Agent not initialized."
                        status.update(label="Error", state="error")
                
                st.markdown(response_text)
            
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})