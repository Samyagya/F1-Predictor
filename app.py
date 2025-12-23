import streamlit as st
import pandas as pd
import joblib
import os
import itertools
import altair as alt

# --- IMPORT YOUR BACKEND LOGIC ---
try:
    from src.physics import get_pit_loss, calculate_tyre_cliff_penalty
    from src.solve_strategy_battle import get_stint_time, load_artifacts, TOTAL_LAPS, COMPOUNDS
except ImportError:
    st.error("Could not import 'src'. Make sure you are running this from the main folder!")
    st.stop()

# --- HELPER: GENERATE LAP DATA FOR PLOTTING ---
def get_race_data(model, encoder, driver, circuit, compounds, pit_laps):
    """
    Re-simulates the race to get lap-by-lap data for the graph.
    """
    lap_data = []
    current_lap = 1
    
    # Define stints based on pit laps
    # If pit_laps = [20], stints are (1-20), (21-57)
    stint_defs = []
    start = 1
    for p in pit_laps:
        stint_defs.append((start, p))
        start = p + 1
    stint_defs.append((start, TOTAL_LAPS))
    
    total_time = 0
    
    for i, (start_lap, end_lap) in enumerate(stint_defs):
        compound = compounds[i]
        laps = list(range(start_lap, end_lap + 1))
        
        # Vectorized Prediction
        data = pd.DataFrame({
            'Driver': driver, 'Circuit': circuit, 'Compound': compound,
            'TyreLife': range(len(laps)), 'LapNumber': laps,
            'Rainfall': 0, 'FuelWeight': [110 * (1 - (l / TOTAL_LAPS)) for l in laps]
        })
        data.loc[data['FuelWeight'] < 0, 'FuelWeight'] = 0
        
        preds = model.predict(encoder.transform(data))
        
        for j, base_time in enumerate(preds):
            tyre_age = j
            penalty = calculate_tyre_cliff_penalty(compound, tyre_age)
            lap_time = base_time + penalty
            
            # Add Pit Cost if it's the pit lap
            if laps[j] in pit_laps:
                lap_time += get_pit_loss(circuit) + 1.5 # Traffic Penalty
                
            lap_data.append(lap_time)
            
    return lap_data

# --- PAGE CONFIG ---
st.set_page_config(page_title="F1 Strategy AI", page_icon="🏎️", layout="wide")

# --- HEADER ---
st.title("🏎️ F1 2026 Strategy Predictor")
st.markdown("### AI-Powered Race Engineer | Physics v3.0 Enabled")

# --- SIDEBAR ---
st.sidebar.header("Race Configuration")
driver = st.sidebar.selectbox("Select Driver", ["VER", "HAM", "LEC", "NOR", "PIA"])
circuit = st.sidebar.selectbox("Select Circuit", ["Sakhir", "Monza", "Silverstone", "Spa", "Monaco"])
pit_loss = get_pit_loss(circuit)
traffic_penalty = 1.5
st.sidebar.info(f"📍 **{circuit} Stats**\n\n* Pit Loss: {pit_loss}s\n* Traffic Cost: {traffic_penalty}s")

# --- MAIN LOGIC ---
if st.button("🚀 Run Strategy Simulation", type="primary"):
    
    with st.spinner("Calculating optimal strategies..."):
        model, encoder = load_artifacts()
    
    col1, col2 = st.columns(2)
    
    # --- 1-STOP SOLVER ---
    best_1stop = {'Time': 999999, 'Desc': '', 'Pit': 0, 'Comps': []}
    perms_1stop = list(itertools.product(COMPOUNDS, repeat=2))
    
    for c1, c2 in perms_1stop:
        if c1 == c2: continue 
        pit_lap = 25 # simplified for speed in UI
        t1 = get_stint_time(model, encoder, driver, circuit, c1, 1, pit_lap)
        t2 = get_stint_time(model, encoder, driver, circuit, c2, pit_lap + 1, TOTAL_LAPS)
        total = t1 + t2 + pit_loss + traffic_penalty
        
        if total < best_1stop['Time']:
            best_1stop = {'Time': total, 'Desc': f"{c1} -> {c2}", 'Pit': [pit_lap], 'Comps': [c1, c2]}

    with col1:
        st.subheader("1️⃣ 1-Stop Strategy")
        m1 = int(best_1stop['Time'] // 60)
        s1 = best_1stop['Time'] % 60
        st.metric("Total Time", f"{m1}m {s1:05.2f}s", delta=best_1stop['Desc'])

    # --- 2-STOP SOLVER ---
    best_2stop = {'Time': 999999, 'Desc': '', 'Pit': [], 'Comps': []}
    perms_2stop = list(itertools.product(COMPOUNDS, repeat=3))
    valid_perms = [p for p in perms_2stop if len(set(p)) >= 2]
    
    for c1, c2, c3 in valid_perms:
        # simplified pit laps for UI speed
        pit1, pit2 = 18, 38
        t1 = get_stint_time(model, encoder, driver, circuit, c1, 1, pit1)
        t2 = get_stint_time(model, encoder, driver, circuit, c2, pit1 + 1, pit2)
        t3 = get_stint_time(model, encoder, driver, circuit, c3, pit2 + 1, TOTAL_LAPS)
        total = t1 + t2 + t3 + (pit_loss * 2) + (traffic_penalty * 2)
        
        if total < best_2stop['Time']:
            best_2stop = {'Time': total, 'Desc': f"{c1} -> {c2} -> {c3}", 'Pit': [pit1, pit2], 'Comps': [c1, c2, c3]}

    with col2:
        st.subheader("2️⃣ 2-Stop Strategy")
        m2 = int(best_2stop['Time'] // 60)
        s2 = best_2stop['Time'] % 60
        st.metric("Total Time", f"{m2}m {s2:05.2f}s", delta=best_2stop['Desc'])

    # --- VERDICT ---
    st.divider()
    diff = best_1stop['Time'] - best_2stop['Time']
    if diff > 0:
        st.success(f"🏆 **2-STOP WINS** by {diff:.2f}s")
    else:
        st.success(f"🏆 **1-STOP WINS** by {abs(diff):.2f}s")

    # --- TELEMETRY GRAPH ---
    st.subheader("📊 Telemetry Analysis: Lap Times")
    
    # Generate Plot Data
    laps_1stop = get_race_data(model, encoder, driver, circuit, best_1stop['Comps'], best_1stop['Pit'])
    laps_2stop = get_race_data(model, encoder, driver, circuit, best_2stop['Comps'], best_2stop['Pit'])
    
    chart_data = pd.DataFrame({
        'Lap': range(1, TOTAL_LAPS + 1),
        '1-Stop Pace': laps_1stop,
        '2-Stop Pace': laps_2stop
    })
    
    st.line_chart(chart_data, x='Lap', y=['1-Stop Pace', '2-Stop Pace'], color=["#FF4B4B", "#00CC96"])
    st.caption("Note: Spikes indicate Pit Stops. Lower is faster.")