import random
import pandas as pd
from src.physics import get_pit_loss
from src.solve_strategy_battle import solve_scenario, load_artifacts

# "Personality" responses
GREETINGS = [
    "Radio check. Loud and clear. How can I help with the strategy?",
    "Pit wall here. I'm ready to run the numbers.",
    "Copy that. I'm online. Ask me about a driver or a full race prediction."
]

UNKNOWN_CMD = [
    "Negative, I didn't copy that. Please specify a Driver and Circuit, or ask 'Who will win in Monaco?'",
    "Telemetry unclear. Try asking: 'Predict the winner of Bahrain' or 'Strategy for Max at Monza'."
]

# FULL 2026 GRID (Needed for full race simulation)
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
        text = user_text.lower()
        
        # 1. DETECT CIRCUIT
        circuit_name = None
        circuits = [
            "sakhir", "bahrain", "jeddah", "monaco", "monza", "silverstone", 
            "spa", "suzuka", "vegas", "miami", "austin", "baku", "madrid",
            "barcelona", "canada", "montreal", "hungary", "hungaroring", 
            "dutch", "zandvoort", "singapore", "mexico", "brazil", "interlagos",
            "qatar", "lusail", "abu dhabi", "yas marina"
        ]
        
        for c in circuits:
            if c in text:
                circuit_name = c.capitalize()
                # Fix common names
                if c == "bahrain": circuit_name = "Sakhir"
                if c == "vegas": circuit_name = "Las Vegas"
                if c == "hungary": circuit_name = "Hungaroring"
                if c == "brazil": circuit_name = "Interlagos"
                if c == "abu dhabi": circuit_name = "Yas Marina"
                break
        
        # 2. DETECT INTENT: "WHO WILL WIN?" (Full Race Sim)
        win_keywords = ["win", "winner", "podium", "predict", "result"]
        is_race_prediction = any(k in text for k in win_keywords)
        
        if is_race_prediction and circuit_name:
            return self.simulate_full_race(circuit_name)

        # 3. DETECT DRIVER (Single Strategy)
        driver_code = None
        driver_name = "Unknown"
        
        # Simplified map for chat
        name_map = {
            "max": "VER", "verstappen": "VER", "lewis": "HAM", "hamilton": "HAM",
            "lando": "NOR", "norris": "NOR", "charles": "LEC", "leclerc": "LEC",
            "oscar": "PIA", "piastri": "PIA", "george": "RUS", "russell": "RUS",
            "kimi": "ANT", "antonelli": "ANT", "fernando": "ALO", "alonso": "ALO",
            "carlos": "SAI", "sainz": "SAI", "alex": "ALB", "albon": "ALB",
            "checo": "PER", "perez": "PER", "bottas": "BOT"
        }
        
        for name, code in name_map.items():
            if name in text:
                driver_code = code
                driver_name = name.capitalize()
                break
                
        # 4. EXECUTE LOGIC
        if "hello" in text or "hi " in text:
            return random.choice(GREETINGS)
            
        if "pit loss" in text and circuit_name:
            loss = get_pit_loss(circuit_name)
            return f"Calculated pit loss for {circuit_name} is **{loss} seconds**."
            
        if driver_code and circuit_name:
            return self.run_single_strategy(driver_code, driver_name, circuit_name)
            
        if is_race_prediction and not circuit_name:
            return "I can predict the winner, but I need a Circuit. (e.g., 'Who wins in Monaco?')"
            
        if driver_code:
            return f"I have {driver_name} on the monitor, but I need a Circuit. (e.g., 'at Monaco')"
            
        if circuit_name:
            return f"I have the data for {circuit_name}. Ask 'Who will win?' or ask about a specific driver."

        return random.choice(UNKNOWN_CMD)

    def run_single_strategy(self, driver_code, driver_name, circuit_name):
        try:
            strat, desc, time = solve_scenario(
                self.model, self.encoder, driver_code, circuit_name, 
                get_pit_loss(circuit_name), 1.5, "", "Standard Q3"
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
            
            # Simulate ALL drivers
            for name, code in DRIVERS.items():
                strat, desc, time = solve_scenario(
                    self.model, self.encoder, code, circuit_name, 
                    pit_loss, 1.5, "", "Standard Q3"
                )
                
                # Apply Skill Bias (same as Tab 1)
                bias = 0
                if code in ["VER", "HAM", "LEC", "NOR"]: bias = -5
                elif code in ["BOT", "HUL", "OCO"]: bias = +10
                
                results.append({"Driver": name, "Time": time + bias, "Strategy": strat})
            
            # Sort
            results.sort(key=lambda x: x['Time'])
            
            # Format Output
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
            
            _Calculated based on 22-car simulation using current physics._
            """
        except Exception as e:
            return f"Simulation failed: {str(e)}"