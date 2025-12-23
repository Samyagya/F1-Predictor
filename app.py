import streamlit as st
import pandas as pd
import joblib
import os
import itertools
import altair as alt

# --- IMPORT BACKEND ---
try:
    from src.physics import get_pit_loss, calculate_tyre_cliff_penalty
    from src.solve_strategy_battle import get_stint_time, load_artifacts, TOTAL_LAPS
    from src.tyre_strategy import get_race_start_tyres
except ImportError:
    st.error("Could not import 'src'. Make sure you are running this from the main folder!")
    st.stop()

# --- CONFIG ---
st.set_page_config(page_title="F1 2026 Oracle", page_icon="🏎️", layout="wide")

DRIVERS = {
    "Max Verstappen": "VER", "Lewis Hamilton": "HAM", "Lando Norris": "NOR", 
    "Charles Leclerc": "LEC", "Oscar Piastri": "PIA", "George Russell": "RUS",
    "Kimi Antonelli": "ANT", "Fernando Alonso": "ALO", "Franco Colapinto": "COL",
    "Liam Lawson": "LAW"
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
    
    # Get Inventory
    tyres = get_race_start_tyres(driver_code, strategy_mode=scenario_mode)
    tyre_indices = range(len(tyres))
    
    # 1-Stop Solver
    best_1stop = {'Time': 999999, 'Desc': ''}
    for idx1, idx2 in itertools.permutations(tyre_indices, 2):
        s1, s2 = tyres[idx1], tyres[idx2]
        if s1['compound'] == s2['compound']: continue
        
        # Check Lap 25 pit window
        t1 = get_stint_time(model, encoder, driver_code, circuit_name, s1, 1, 25)
        t2 = get_stint_time(model, encoder, driver_code, circuit_name, s2, 26, TOTAL_LAPS)
        total = t1 + t2 + pit_loss + traffic
        
        if total < best_1stop['Time']:
            best_1stop = {'Time': total, 'Desc': f"{s1['compound']} ({s1['status']}) -> {s2['compound']} ({s2['status']})"}

    # 2-Stop Solver
    best_2stop = {'Time': 999999, 'Desc': ''}
    # Optimized permutation filter
    valid_perms = [
        p for p in itertools.permutations(tyre_indices, 3) 
        if len({tyres[i]['compound'] for i in p}) >= 2
    ]
    
    for idx1, idx2, idx3 in valid_perms:
        s1, s2, s3 = tyres[idx1], tyres[idx2], tyres[idx3]
        
        # Fixed stops (Lap 18, 38)
        t1 = get_stint_time(model, encoder, driver_code, circuit_name, s1, 1, 18)
        t2 = get_stint_time(model, encoder, driver_code, circuit_name, s2, 19, 38)
        t3 = get_stint_time(model, encoder, driver_code, circuit_name, s3, 39, TOTAL_LAPS)
        total = t1 + t2 + t3 + (pit_loss * 2) + (traffic * 2)
        
        if total < best_2stop['Time']:
            best_2stop = {'Time': total, 'Desc': f"{s1['compound']} ({s1['status']}) -> {s2['compound']} ({s2['status']}) -> {s3['compound']} ({s3['status']})"}
            
    # Return Winner
    if best_2stop['Time'] < best_1stop['Time']:
        return "2-STOP", best_2stop['Desc'], best_2stop['Time']
    else:
        return "1-STOP", best_1stop['Desc'], best_1stop['Time']

# --- DASHBOARD UI ---
st.title("🏎️ F1 2026 Strategy Oracle")
st.markdown("### Race Weekend Simulator")

# Sidebar Controls
with st.sidebar:
    st.header("Setup")
    sel_driver = st.selectbox("Driver", list(DRIVERS.keys()))
    sel_circuit = st.selectbox("Circuit", CIRCUITS)
    st.divider()
    st.info(f"**{sel_circuit} Data**\n\n* Pit Loss: {get_pit_loss(sel_circuit)}s\n* Tyre Stress: High")

# Main Action
if st.button("🔮 Analyze Weekend Scenarios", type="primary"):
    
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
            
            # Formating Time
            m = int(race_time // 60)
            s = race_time % 60
            
            # Styling based on winner
            card_color = "green" if strategy_type == "2-STOP" else "blue"
            if "SOFT" in strategy_desc and "NEW" in strategy_desc:
                badge = "🔥 ATTACK MODE"
            else:
                badge = "🛡️ DEFENSIVE"

            # Render Card
            with st.container():
                st.markdown(f"#### {title}")
                st.caption(note)
                
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.success(f"**{strategy_type}:** {strategy_desc}")
                with col_b:
                    st.metric("Total Time", f"{m}m {s:05.2f}s")
                
                st.divider()