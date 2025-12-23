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

# --- HELPER: TIME FORMATTER (HH:MM:SS) ---
def format_time(seconds):
    """Converts seconds to '1h 32m 12.45s' format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs:05.2f}s"
    else:
        return f"{minutes}m {secs:05.2f}s"

# --- HELPER: RUN ONE SCENARIO ---
def run_scenario_analysis(driver_code, circuit_name, scenario_mode):
    model, encoder = load_artifacts()
    pit_loss = get_pit_loss(circuit_name)
    traffic = 1.5
    return solve_scenario(model, encoder, driver_code, circuit_name, pit_loss, traffic, "", scenario_mode)

# --- UI START ---
st.title("🏎️ F1 2026 Strategy Oracle")

# TABS
tab1, tab2 = st.tabs(["🔮 Next Race Predictor", "🛠️ Strategy Workbench"])

# =========================================================
# TAB 1: NEXT RACE PREDICTOR
# =========================================================
with tab1:
    next_race = get_next_race()
    circuit_next = next_race['circuit']
    
    # Format Date
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
        
        # Simulate Grid
        for i, (name, code) in enumerate(driver_list):
            strat, desc, time = run_scenario_analysis(code, circuit_next, "Standard Q3")
            
            # Skill Bias (Optional)
            bias = 0
            if code in ["VER", "HAM", "LEC", "NOR"]: bias = -5
            elif code in ["BOT", "HUL", "OCO"]: bias = +10
            
            final_time = time + bias
            
            results.append({
                "Driver": name,
                "Strategy": strat,
                "Time_Sec": final_time # Keep raw float for sorting
            })
            progress_bar.progress((i + 1) / total_drivers)
            
        # Sort by Fastest Time
        results.sort(key=lambda x: x['Time_Sec'])
        
        # CALCULATE GAPS & FORMAT TIME
        winner_time = results[0]['Time_Sec']
        
        final_table = []
        for res in results:
            gap = res['Time_Sec'] - winner_time
            
            # Format Gap
            if gap == 0:
                gap_str = "LEADER"
            else:
                gap_str = f"+{gap:.3f}s"
                
            final_table.append({
                "Driver": res['Driver'],
                "Strategy": res['Strategy'],
                "Race Time": format_time(res['Time_Sec']),
                "Gap": gap_str
            })
        
        # --- DISPLAY PODIUM ---
        st.success("🏁 Simulation Complete!")
        
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
            
        # --- FULL CLASSIFICATION TABLE ---
        st.divider()
        st.subheader("Full Race Classification")
        
        df_display = pd.DataFrame(final_table)
        df_display.index += 1
        st.dataframe(df_display, use_container_width=True)

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
                
                with st.container():
                    st.markdown(f"#### {title}")
                    st.caption(note)
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.success(f"**{strategy_type}:** {strategy_desc}")
                    with col_b:
                        st.metric("Total Time", format_time(race_time))
                    st.divider()