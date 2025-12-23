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
    from src.calendar_utils import get_next_race 
except ImportError:
    st.error("Could not import 'src'. Make sure you are running this from the main folder!")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="F1 2026 Oracle", page_icon="🏎️", layout="wide")

# --- FULL 2026 GRID (22 DRIVERS) ---
DRIVERS = {
    # Red Bull
    "Max Verstappen (Red Bull)": "VER",
    "Isack Hadjar (Red Bull)": "HAD",
    # Mercedes
    "George Russell (Mercedes)": "RUS",
    "Kimi Antonelli (Mercedes)": "ANT",
    # Ferrari
    "Charles Leclerc (Ferrari)": "LEC",
    "Lewis Hamilton (Ferrari)": "HAM",
    # McLaren
    "Lando Norris (McLaren)": "NOR",
    "Oscar Piastri (McLaren)": "PIA",
    # Aston Martin
    "Fernando Alonso (Aston Martin)": "ALO",
    "Lance Stroll (Aston Martin)": "STR",
    # Alpine
    "Pierre Gasly (Alpine)": "GAS",
    "Franco Colapinto (Alpine)": "COL",
    # Williams
    "Carlos Sainz (Williams)": "SAI",
    "Alex Albon (Williams)": "ALB",
    # RB (Racing Bulls)
    "Liam Lawson (RB)": "LAW",
    "Arvid Lindblad (RB)": "LIN",
    # Haas
    "Esteban Ocon (Haas)": "OCO",
    "Ollie Bearman (Haas)": "BEA",
    # Audi (Sauber)
    "Nico Hulkenberg (Audi)": "HUL",
    "Gabriel Bortoleto (Audi)": "BOR",
    # Cadillac (New Team)
    "Sergio Perez (Cadillac)": "PER",
    "Valtteri Bottas (Cadillac)": "BOT"
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
# TAB 1: NEXT RACE PREDICTOR
# =========================================================
with tab1:
    next_race = get_next_race()
    circuit_next = next_race['circuit']
    
    # FORMAT DATE AS DD-MM-YYYY
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
        
        # Simulate every driver
        for i, (name, code) in enumerate(driver_list):
            strat, desc, time = run_scenario_analysis(code, circuit_next, "Standard Q3")
            
            # Simple "Driver Skill" Bias (Optional tweak for realism)
            # This helps separate top cars from backmarkers in a 'tie'
            bias = 0
            if code in ["VER", "HAM", "LEC", "NOR"]: bias = -5 # Top tier bonus
            elif code in ["BOT", "HUL", "OCO"]: bias = +10 # Backmarker penalty
            
            final_time = time + bias
            
            results.append({
                "Driver": name,
                "Strategy": strat,
                "Time_Sec": final_time,
                "Display_Time": f"{int(final_time//60)}m {final_time%60:.2f}s"
            })
            progress_bar.progress((i + 1) / total_drivers)
            
        # Sort by Fastest Time
        results.sort(key=lambda x: x['Time_Sec'])
        
        # --- DISPLAY PODIUM ---
        st.success("🏁 Simulation Complete!")
        
        c1, c2, c3 = st.columns(3)
        with c2: # Winner (Center)
            st.markdown(f"### 🥇 1st Place")
            st.metric(label=results[0]['Driver'], value=results[0]['Display_Time'])
            
        with c1: # 2nd (Left)
            st.markdown(f"### 🥈 2nd Place")
            st.metric(label=results[1]['Driver'], value=f"+{(results[1]['Time_Sec'] - results[0]['Time_Sec']):.2f}s")
            
        with c3: # 3rd (Right)
            st.markdown(f"### 🥉 3rd Place")
            st.metric(label=results[2]['Driver'], value=f"+{(results[2]['Time_Sec'] - results[0]['Time_Sec']):.2f}s")
            
        # --- FULL CLASSIFICATION TABLE ---
        st.divider()
        st.subheader("Full Race Classification")
        
        df_results = pd.DataFrame(results).drop(columns=['Time_Sec'])
        df_results.index += 1
        st.dataframe(df_results, use_container_width=True)

# =========================================================
# TAB 2: STRATEGY WORKBENCH
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