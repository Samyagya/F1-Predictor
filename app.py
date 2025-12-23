import streamlit as st
import pandas as pd
import joblib
import os
import itertools
import altair as alt
from datetime import datetime

# --- IMPORT BACKEND ---
try:
    from src.physics import get_pit_loss, calculate_tyre_cliff_penalty
    from src.solve_strategy_battle import get_stint_time, load_artifacts, TOTAL_LAPS, solve_scenario
    from src.tyre_strategy import get_race_start_tyres
    from src.calendar_utils import get_next_race # NEW IMPORT
except ImportError:
    st.error("Could not import 'src'. Make sure you are running this from the main folder!")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="F1 2026 Oracle", page_icon="🏎️", layout="wide")

DRIVERS = {
    "Max Verstappen": "VER", "Lewis Hamilton": "HAM", "Lando Norris": "NOR", 
    "Charles Leclerc": "LEC", "Oscar Piastri": "PIA", "George Russell": "RUS",
    "Kimi Antonelli": "ANT", "Fernando Alonso": "ALO", "Franco Colapinto": "COL",
    "Liam Lawson": "LAW", "Alex Albon": "ALB", "Carlos Sainz": "SAI",
    "Pierre Gasly": "GAS", "Lance Stroll": "STR", "Esteban Ocon": "OCO",
    "Nico Hulkenberg": "HUL", "Yuki Tsunoda": "TSU"
} 

CIRCUITS = [
    "Sakhir", "Jeddah", "Albert Park", "Suzuka", "Shanghai", "Miami",
    "Imola", "Monaco", "Montreal", "Barcelona", "Red Bull Ring",
    "Silverstone", "Hungaroring", "Spa", "Zandvoort", "Monza",
    "Baku", "Singapore", "Austin", "Mexico City", "Las Vegas", "Yas Marina"
]

# --- HELPER: RUN ONE SCENARIO ---
def run_scenario_analysis(driver_code, circuit_name, scenario_mode):
    model, encoder = load_artifacts()
    pit_loss = get_pit_loss(circuit_name)
    traffic = 1.5
    return solve_scenario(model, encoder, driver_code, circuit_name, pit_loss, traffic, "", scenario_mode)

# --- UI START ---
st.title("🏎️ F1 2026 Strategy Oracle")

# TABS FOR NAVIGATION
tab1, tab2 = st.tabs(["🔮 Next Race Predictor", "🛠️ Strategy Workbench"])

# =========================================================
# TAB 1: NEXT RACE PREDICTOR (The New Feature)
# =========================================================
with tab1:
    next_race = get_next_race()
    circuit_next = next_race['circuit']
    date_next = next_race['date']
    
    st.header(f"Next Grand Prix: {circuit_next} 🇧🇭")
    st.caption(f"Scheduled for: {date_next}")
    
    if st.button("🏆 Predict Race Winner", type="primary"):
        st.write(f"Simulating full grid battle at **{circuit_next}**...")
        
        # Progress Bar because simulating 20 drivers takes time
        progress_bar = st.progress(0)
        results = []
        
        # Run Simulation for every driver (Assuming Q3 'Used Softs' start for fairness)
        driver_list = list(DRIVERS.items())
        total_drivers = len(driver_list)
        
        for i, (name, code) in enumerate(driver_list):
            # Run the AI
            strat, desc, time = run_scenario_analysis(code, circuit_next, "Standard Q3")
            results.append({
                "Driver": name,
                "Code": code,
                "Strategy": strat,
                "Time_Sec": time,
                "Display_Time": f"{int(time//60)}m {time%60:.2f}s"
            })
            progress_bar.progress((i + 1) / total_drivers)
            
        # Sort by Fastest Time (Lowest Seconds)
        results.sort(key=lambda x: x['Time_Sec'])
        
        # --- DISPLAY PODIUM ---
        st.success("🏁 Simulation Complete!")
        
        c1, c2, c3 = st.columns(3)
        with c2:
            st.markdown(f"### 🥇 1st Place")
            st.image(f"https://media.formula1.com/content/dam/fom-website/drivers/2024/Drivers/{results[0]['Driver'].split()[-1].upper()}.jpg.img.1024.medium.jpg/1708.jpg", width=150)
            st.metric(label=results[0]['Driver'], value=results[0]['Display_Time'])
            
        with c1:
            st.markdown(f"### 🥈 2nd Place")
            st.metric(label=results[1]['Driver'], value=f"+{(results[1]['Time_Sec'] - results[0]['Time_Sec']):.2f}s")
            
        with c3:
            st.markdown(f"### 🥉 3rd Place")
            st.metric(label=results[2]['Driver'], value=f"+{(results[2]['Time_Sec'] - results[0]['Time_Sec']):.2f}s")
            
        # --- FULL CLASSIFICATION TABLE ---
        st.divider()
        st.subheader("Full Race Classification")
        
        df_results = pd.DataFrame(results).drop(columns=['Time_Sec', 'Code'])
        df_results.index += 1 # Start rank at 1
        st.dataframe(df_results, use_container_width=True)

# =========================================================
# TAB 2: STRATEGY WORKBENCH (Your Existing Tool)
# =========================================================
with tab2:
    st.markdown("### Race Weekend Simulator")
    
    # Sidebar Controls (Moved here so they don't clutter Tab 1)
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
                m = int(race_time // 60)
                s = race_time % 60
                
                with st.container():
                    st.markdown(f"#### {title}")
                    st.caption(note)
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.success(f"**{strategy_type}:** {strategy_desc}")
                    with col_b:
                        st.metric("Total Time", f"{m}m {s:05.2f}s")
                    st.divider()