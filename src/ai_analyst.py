import random
import pandas as pd
from src.physics import get_pit_loss
from src.solve_strategy_battle import solve_scenario, load_artifacts

# ... (Keep GREETINGS, UNKNOWN_CMD, and DRIVERS the same as before) ...
# COPY PASTE YOUR DRIVERS DICTIONARY HERE FROM PREVIOUS STEPS
DRIVERS = {
    "Max Verstappen": "VER", "Isack Hadjar": "HAD",
    "George Russell": "RUS", "Kimi Antonelli": "ANT",
    "Charles Leclerc": "LEC", "Lewis Hamilton": "HAM",
    "Lando Norris": "NOR", "Oscar Piastri": "PIA",
    "Fernando Alonso": "ALO", "Lance Stroll": "STR",
    "Pierre Gasly": "GAS", "Franco Colapinto": "COL",
    "Carlos Sainz": "SAI", "Alex Albon": "ALB",
    "Liam Lawson": "LAW", "Arvid Lindblad": "LIN",
    "Esteban Ocon": "OCO", "Ollie Bearman": "BEA",
    "Nico Hulkenberg": "HUL", "Gabriel Bortoleto": "BOR",
    "Sergio Perez": "PER", "Valtteri Bottas": "BOT"
}

class RaceEngineerAI:
    def __init__(self):
        self.model, self.encoder = load_artifacts()

    def analyze_query(self, user_text):
        # ... (Keep your existing analysis logic exactly the same) ...
        # (Just ensure simulate_full_race is called correctly below)
        text = user_text.lower()
        
        # 1. DETECT CIRCUIT (Keep same code as before)
        circuit_name = None
        circuits = ["sakhir", "bahrain", "jeddah", "monaco", "monza", "silverstone", "spa", "suzuka", "vegas", "miami", "austin", "baku", "madrid", "barcelona", "canada", "montreal", "hungary", "zandvoort", "singapore", "mexico", "brazil", "interlagos", "qatar", "abu dhabi", "yas marina"]
        
        for c in circuits:
            if c in text:
                circuit_name = c.capitalize()
                if c == "bahrain": circuit_name = "Sakhir"
                # ... other fixes ...
                break
        
        win_keywords = ["win", "winner", "podium", "predict", "result"]
        is_race_prediction = any(k in text for k in win_keywords)
        
        if is_race_prediction and circuit_name:
            return self.simulate_full_race(circuit_name)
            
        # ... (Rest of detection logic) ...
        # If you need the full file again, let me know, but mainly we update simulate_full_race below:
        
        # FOR BREVITY in this snippet, I assume you kept the analyze_query logic 
        # from the previous step. If not, paste the previous ai_analyst.py content 
        # and replace ONLY simulate_full_race.
        
        # 3. DETECT DRIVER (Single Strategy)
        driver_code = None
        driver_name = "Unknown"
        name_map = {"max": "VER", "lewis": "HAM", "lando": "NOR"} # ... add full map
        for name, code in name_map.items():
            if name in text:
                driver_code = code
                driver_name = name.capitalize()
                break
                
        if driver_code and circuit_name:
            return self.run_single_strategy(driver_code, driver_name, circuit_name)
            
        return "I need a Driver and a Circuit."

    def run_single_strategy(self, driver_code, driver_name, circuit_name):
        try:
            # Single strategy is fast, so fast_mode=False is fine for accuracy
            strat, desc, time = solve_scenario(
                self.model, self.encoder, driver_code, circuit_name, 
                get_pit_loss(circuit_name), 1.5, "", "Standard Q3", fast_mode=False
            )
            m = int(time // 60)
            s = time % 60
            return f"**Strategy for {driver_name} @ {circuit_name}:**\n\nAI recommends: **{strat}**\n* `{desc}`\n* Race Time: {m}m {s:.2f}s"
        except Exception as e:
            return f"Telemetry Error: {str(e)}"

    def simulate_full_race(self, circuit_name):
        try:
            results = []
            pit_loss = get_pit_loss(circuit_name)
            
            # Simulate ALL drivers using FAST MODE
            for name, code in DRIVERS.items():
                # fast_mode=True is the key here!
                strat, desc, time = solve_scenario(
                    self.model, self.encoder, code, circuit_name, 
                    pit_loss, 1.5, "", "Standard Q3", fast_mode=True
                )
                
                bias = 0
                if code in ["VER", "HAM", "LEC", "NOR"]: bias = -5
                elif code in ["BOT", "HUL", "OCO"]: bias = +10
                
                results.append({"Driver": name, "Time": time + bias, "Strategy": strat})
            
            results.sort(key=lambda x: x['Time'])
            
            winner = results[0]
            p2 = results[1]
            p3 = results[2]
            
            gap2 = p2['Time'] - winner['Time']
            gap3 = p3['Time'] - winner['Time']
            
            return f"""
            ### 🏁 Race Prediction: {circuit_name}
            
            **🥇 WINNER:** {winner['Driver']} ({winner['Strategy']})
            **🥈 P2:** {p2['Driver']} (+{gap2:.2f}s)
            **🥉 P3:** {p3['Driver']} (+{gap3:.2f}s)
            
            _Calculated based on 22-car simulation (Turbo Mode)._
            """
        except Exception as e:
            return f"Simulation failed: {str(e)}"