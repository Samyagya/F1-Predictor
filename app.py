import sys
import os
import streamlit as st
import pandas as pd
from datetime import datetime

# Force python to find the 'src' folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORT BACKEND ---
try:
    from src.physics import get_pit_loss
    from src.solve_strategy_battle import solve_scenario, load_artifacts
    from src.calendar_utils import get_next_race 
    from src.llm_agent import F1Agent
except Exception as e:
    st.error(f"CRITICAL ERROR: {e}")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="F1 2026 Oracle", page_icon="🏎️", layout="wide")

# --- SECRETS MANAGEMENT ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        api_key = st.text_input("Enter Gemini API Key", type="password")

# --- FULL 2026 GRID ---
DRIVERS = {
    "Max Verstappen (Red Bull)": "VER", "Isack Hadjar (Red Bull)": "HAD",
    "George Russell (Mercedes)": "RUS", "Kimi Antonelli (Mercedes)": "ANT",
    "Charles Leclerc (Ferrari)": "LEC", "Lewis Hamilton (Ferrari)": "HAM",
    "Lando Norris (McLaren)": "NOR", "Oscar Piastri (McLaren)": "PIA",
    "Fernando Alonso (Aston Martin)": "ALO", "Lance Stroll (Aston Martin)": "STR",
    "Pierre Gasly (Alpine)": "GAS", "Franco Colapinto (Alpine)": "COL",
    "Carlos Sainz (Williams)": "SAI", "Alex Albon (Williams)": "ALB",
    "Liam Lawson (RB)": "LAW", "Arvid Lindblad (RB)": "LIN",
    "Esteban Ocon (Haas)": "OCO", "Ollie Bearman (Haas)": "BEA",
    "Nico Hulkenberg (Audi)": "HUL", "Gabriel Bortoleto (Audi)": "BOR",
    "Sergio Perez (Cadillac)": "PER", "Valtteri Bottas (Cadillac)": "BOT"
}

CIRCUITS = [
    "Sakhir", "Jeddah", "Albert Park", "Suzuka", "Shanghai", "Miami",
    "Imola", "Monaco", "Montreal", "Barcelona", "Red Bull Ring",
    "Silverstone", "Hungaroring", "Spa", "Zandvoort", "Monza",
    "Baku", "Singapore", "Austin", "Mexico City", "Las Vegas", "Yas Marina"
]

# --- HELPER: TIME FORMATTER ---
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}h {minutes}m {secs:05.2f}s" if hours > 0 else f"{minutes}m {secs:05.2f}s"

# --- HELPER: RUN SCENARIO ---
def run_scenario_analysis(driver_code, circuit_name, scenario_mode):
    model, encoder = load_artifacts()
    pit_loss = get_pit_loss(circuit_name)
    traffic = 1.5
    return solve_scenario(model, encoder, driver_code, circuit_name, pit_loss, traffic, "", scenario_mode)

# --- INITIALIZE CHAT ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Radio check. I am connected to the simulation engine. What's the plan?"}
    ]

if "agent" not in st.session_state and api_key:
    try:
        st.session_state.agent = F1Agent(api_key)
    except Exception as e:
        st.error(f"Failed to initialize AI: {e}")

# --- TABS ---
st.title("🏎️ F1 2026 Strategy Oracle")
tab1, tab2, tab3 = st.tabs(["🔮 Next Race", "🛠️ Workbench", "💬 AI Engineer"])

# =========================================================
# TAB 1: NEXT RACE PREDICTOR
# =========================================================
with tab1:
    next_race = get_next_race()
    circuit_next = next_race['circuit']
    raw_date = datetime.strptime(next_race['date'], "%Y-%m-%d")
    formatted_date = raw_date.strftime("%d-%m-%Y")
    
    st.header(f"Next Grand Prix: {circuit_next}")
    st.caption(f"Scheduled for: **{formatted_date}**")
    
    if st.button("🏆 Predict Race Winner", type="primary"):
        st.write(f"Simulating full 22-car grid battle at **{circuit_next}**...")
        progress_bar = st.progress(0)
        results = []
        driver_list = list(DRIVERS.items())
        total_drivers = len(driver_list)
        
        for i, (name, code) in enumerate(driver_list):
            strat, desc, time = run_scenario_analysis(code, circuit_next, "Standard Q3")
            bias = 0
            if code in ["VER", "HAM", "LEC", "NOR"]: bias = -5
            elif code in ["BOT", "HUL", "OCO"]: bias = +10
            final_time = time + bias
            results.append({"Driver": name, "Strategy": strat, "Time_Sec": final_time})
            progress_bar.progress((i + 1) / total_drivers)
            
        results.sort(key=lambda x: x['Time_Sec'])
        winner_time = results[0]['Time_Sec']
        
        final_table = []
        for res in results:
            gap = res['Time_Sec'] - winner_time
            gap_str = "LEADER" if gap == 0 else f"+{gap:.3f}s"
            final_table.append({
                "Driver": res['Driver'],
                "Strategy": res['Strategy'],
                "Race Time": format_time(res['Time_Sec']),
                "Gap": gap_str
            })
        
        c1, c2, c3 = st.columns(3)
        with c2: 
            st.markdown(f"### 🥇 1st Place")
            st.metric(label=final_table[0]['Driver'], value=final_table[0]['Race Time'])
        with c1: 
            st.markdown(f"### 🥈 2nd Place")
            st.metric(label=final_table[1]['Driver'], value=final_table[1]['Gap'])
        with c3: 
            st.markdown(f"### 🥉 3rd Place")
            st.metric(label=final_table[2]['Driver'], value=final_table[2]['Gap'])
            
        st.divider()
        st.subheader("Full Race Classification")
        df_display = pd.DataFrame(final_table)
        df_display.index += 1
        st.dataframe(df_display, use_container_width=True)

# =========================================================
# TAB 2: STRATEGY WORKBENCH (RESTORED)
# =========================================================
with tab2:
    st.markdown("### Race Weekend Simulator")
    c1, c2 = st.columns(2)
    with c1:
        sel_driver = st.selectbox("Select Driver", list(DRIVERS.keys()), key="wb_driver")
    with c2:
        sel_circuit = st.selectbox("Select Circuit", CIRCUITS, key="wb_circuit")
        
    if st.button("Analyze Scenarios", key="btn_wb"):
        driver_code = DRIVERS[sel_driver]
        scenarios = [
            ("QUALIFIED P1-P10 (Q3)", "Standard Q3", "⚠️ Used Softs available"),
            ("QUALIFIED P11-P15 (Q2)", "Knocked out in Q2", "✅ Some Fresh Softs"),
            ("QUALIFIED P16-P20 (Q1)", "Knocked out in Q1", "🔥 Full Fresh Softs")
        ]
        
        st.subheader(f"Strategic Report: {sel_driver} @ {sel_circuit}")
        for title, mode, note in scenarios:
            with st.spinner(f"Simulating {title}..."):
                strategy_type, strategy_desc, race_time = run_scenario_analysis(driver_code, sel_circuit, mode)
                with st.container():
                    st.markdown(f"#### {title}")
                    st.caption(note)
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.success(f"**{strategy_type}:** {strategy_desc}")
                    with col_b:
                        st.metric("Total Time", format_time(race_time))
                    st.divider()

# =========================================================
# TAB 3: AI RACE ENGINEER (LLM POWERED)
# =========================================================
with tab3:
    st.header("💬 Intelligent Pit Wall")
    
    if not api_key:
        st.info("Please configure the API Key to use the chatbot.")
    else:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask anything: 'Strategy for Max if he has no softs?'"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.status("🧠 Thinking & Simulating...", expanded=True) as status:
                    if "agent" in st.session_state:
                        response_text = st.session_state.agent.ask(prompt)
                        status.update(label="Transmission Received", state="complete", expanded=False)
                    else:
                        response_text = "Connection Error: Agent not initialized (Check API Key)."
                        status.update(label="Error", state="error")
                
                st.markdown(response_text)
            
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})