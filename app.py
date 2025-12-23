import streamlit as st
import pandas as pd
import joblib
import os
import itertools
import altair as alt

# --- IMPORT BACKEND ---
try:
    from src.physics import get_pit_loss, calculate_tyre_cliff_penalty
    from src.solve_strategy_battle import get_stint_time, load_artifacts, TOTAL_LAPS, COMPOUNDS
except ImportError:
    st.error("Could not import 'src'. Make sure you are running this from the main folder!")
    st.stop()

# --- 2026 GRID ROSTER (CONFIRMED & PROJECTED) ---
DRIVERS = {
    # TOP TEAMS
    "Max Verstappen (Red Bull)": "VER",
    "Isack Hadjar (Red Bull)": "HAD",   # Promoted
    "Lewis Hamilton (Ferrari)": "HAM",  # The big move
    "Charles Leclerc (Ferrari)": "LEC",
    "Lando Norris (McLaren)": "NOR",
    "Oscar Piastri (McLaren)": "PIA",
    "George Russell (Mercedes)": "RUS",
    "Kimi Antonelli (Mercedes)": "ANT", # Rookie
    
    # ASTON & ALPINE
    "Fernando Alonso (Aston Martin)": "ALO",
    "Lance Stroll (Aston Martin)": "STR",
    "Pierre Gasly (Alpine)": "GAS",
    "Franco Colapinto (Alpine)": "COL", # New Signing
    
    # MIDFIELD / NEW ENTRIES
    "Carlos Sainz (Williams)": "SAI",
    "Alex Albon (Williams)": "ALB",
    "Nico Hulkenberg (Audi)": "HUL",    # New Team (ex-Sauber)
    "Gabriel Bortoleto (Audi)": "BOR",  # Rookie
    "Esteban Ocon (Haas)": "OCO",
    "Ollie Bearman (Haas)": "BEA",      # Rookie
    "Liam Lawson (RB)": "LAW",
    "Arvid Lindblad (RB)": "LIN",       # Rookie
    
    # THE 11TH TEAM (CADILLAC)
    "Sergio Perez (Cadillac)": "PER",   # New Team
    "Valtteri Bottas (Cadillac)": "BOT"
}

# --- 2026 CALENDAR (24 RACES) ---
# Note: Imola dropped, Madrid added.
CIRCUITS = [
    "Albert Park", "Shanghai", "Suzuka", "Sakhir", "Jeddah", 
    "Miami", "Montreal", "Monaco", "Barcelona", "Red Bull Ring",
    "Silverstone", "Spa", "Hungaroring", "Zandvoort", "Monza",
    "Madrid", # NEW TRACK
    "Baku", "Singapore", "Austin", "Mexico City", "Interlagos",
    "Las Vegas", "Lusail", "Yas Marina"
]

# --- HELPER: PLOT DATA ---
def get_race_data(model, encoder, driver, circuit, compounds, pit_laps):
    lap_data = []
    
    # Reconstruct Stints
    stint_defs = []
    start = 1
    for p in pit_laps:
        stint_defs.append((start, p))
        start = p + 1
    stint_defs.append((start, TOTAL_LAPS))
    
    for i, (start_lap, end_lap) in enumerate(stint_defs):
        compound = compounds[i]
        laps = list(range(start_lap, end_lap + 1))
        
        # Physics Inputs
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
            
            # Pit Penalty
            if laps[j] in pit_laps:
                lap_time += get_pit_loss(circuit) + 1.5
                
            lap_data.append(lap_time)
            
    return lap_data

# --- APP LAYOUT ---
st.set_page_config(page_title="F1 2026 Strategist", page_icon="🏎️", layout="wide")

st.title("🏎️ F1 2026 Strategy Predictor")
st.markdown("### AI-Powered Race Engineer | Season 2026 Spec")
st.caption("Updated with Madrid GP, Audi, Cadillac, and full Driver Market transfers.")

# --- SIDEBAR ---
st.sidebar.header("2026 Race Settings")

# 1. Driver Select
driver_name = st.sidebar.selectbox("Select Driver", list(DRIVERS.keys()))
driver_code = DRIVERS[driver_name]

# 2. Circuit Select
circuit_name = st.sidebar.selectbox("Select Circuit", CIRCUITS)

# 3. Stats Display
pit_loss = get_pit_loss(circuit_name)
traffic = 1.5
st.sidebar.divider()
st.sidebar.markdown(f"""
**📍 {circuit_name} Data**
* Pit Loss: `{pit_loss}s`
* Traffic Pen: `{traffic}s`
""")

# --- MAIN BUTTON ---
if st.button("🚀 Analyze Strategy", type="primary"):
    
    with st.spinner(f"Simulating {TOTAL_LAPS} laps for {driver_code} at {circuit_name}..."):
        model, encoder = load_artifacts()
    
    col1, col2 = st.columns(2)
    
    # --- 1-STOP OPTIMIZER ---
    best_1stop = {'Time': 999999, 'Desc': '', 'Pit': [], 'Comps': []}
    perms_1stop = list(itertools.product(COMPOUNDS, repeat=2))
    
    for c1, c2 in perms_1stop:
        if c1 == c2: continue
        pit_lap = 25 
        t1 = get_stint_time(model, encoder, driver_code, circuit_name, c1, 1, pit_lap)
        t2 = get_stint_time(model, encoder, driver_code, circuit_name, c2, pit_lap + 1, TOTAL_LAPS)
        total = t1 + t2 + pit_loss + traffic
        
        if total < best_1stop['Time']:
            best_1stop = {'Time': total, 'Desc': f"{c1} -> {c2}", 'Pit': [pit_lap], 'Comps': [c1, c2]}

    with col1:
        st.subheader("1️⃣ 1-Stop Strategy")
        st.info(f"**{best_1stop['Desc']}**")
        m1 = int(best_1stop['Time'] // 60)
        s1 = best_1stop['Time'] % 60
        st.metric("Total Race Time", f"{m1}m {s1:05.2f}s")

    # --- 2-STOP OPTIMIZER ---
    best_2stop = {'Time': 999999, 'Desc': '', 'Pit': [], 'Comps': []}
    perms_2stop = list(itertools.product(COMPOUNDS, repeat=3))
    valid_perms = [p for p in perms_2stop if len(set(p)) >= 2]
    
    for c1, c2, c3 in valid_perms:
        pit1, pit2 = 18, 38
        t1 = get_stint_time(model, encoder, driver_code, circuit_name, c1, 1, pit1)
        t2 = get_stint_time(model, encoder, driver_code, circuit_name, c2, pit1 + 1, pit2)
        t3 = get_stint_time(model, encoder, driver_code, circuit_name, c3, pit2 + 1, TOTAL_LAPS)
        total = t1 + t2 + t3 + (pit_loss * 2) + (traffic * 2)
        
        if total < best_2stop['Time']:
            best_2stop = {'Time': total, 'Desc': f"{c1} -> {c2} -> {c3}", 'Pit': [pit1, pit2], 'Comps': [c1, c2, c3]}

    with col2:
        st.subheader("2️⃣ 2-Stop Strategy")
        st.success(f"**{best_2stop['Desc']}**")
        m2 = int(best_2stop['Time'] // 60)
        s2 = best_2stop['Time'] % 60
        st.metric("Total Race Time", f"{m2}m {s2:05.2f}s", delta=f"{best_2stop['Time'] - best_1stop['Time']:.2f}s vs 1-Stop")

    # --- GRAPH ---
    st.divider()
    st.subheader("📊 Telemetry: Pace Comparison")
    
    laps_1stop = get_race_data(model, encoder, driver_code, circuit_name, best_1stop['Comps'], best_1stop['Pit'])
    laps_2stop = get_race_data(model, encoder, driver_code, circuit_name, best_2stop['Comps'], best_2stop['Pit'])
    
    df_plot = pd.DataFrame({
        'Lap': range(1, TOTAL_LAPS + 1),
        '1-Stop Pace': laps_1stop,
        '2-Stop Pace': laps_2stop
    })
    
    st.line_chart(df_plot, x='Lap', y=['1-Stop Pace', '2-Stop Pace'], color=["#FF4B4B", "#00CC96"])