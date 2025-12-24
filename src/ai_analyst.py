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

# FULL 2026 GRID
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

    def extract_entities(self, text):
        """Helper to find Drivers, Circuits, and Intents in a string."""
        text = text.lower()
        
        # 1. DETECT CIRCUIT
        circuit_name = None
        circuits = ["sakhir", "bahrain", "jeddah", "monaco", "monza", "silverstone", "spa", "suzuka", "vegas", "miami", "austin", "baku", "madrid", "barcelona", "canada", "montreal", "hungary", "zandvoort", "singapore", "mexico", "brazil", "interlagos", "qatar", "abu dhabi", "yas marina"]
        
        for c in circuits:
            if c in text:
                circuit_name = c.capitalize()
                if c == "bahrain": circuit_name = "Sakhir"
                if c == "vegas": circuit_name = "Las Vegas"
                if c == "hungary": circuit_name = "Hungaroring"
                if c == "brazil": circuit_name = "Interlagos"
                if c == "abu dhabi": circuit_name = "Yas Marina"
                break

        # 2. DETECT DRIVER
        driver_code = None
        driver_name = None
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

        # 3. DETECT INTENT
        win_keywords = ["win", "winner", "podium", "predict", "result"]
        is_race_prediction = any(k in text for k in win_keywords)
        
        return driver_code, driver_name, circuit_name, is_race_prediction

    def analyze_query(self, user_text, chat_history=[]):
        """
        Analyzes query with Context Awareness.
        If data is missing in 'user_text', it looks back at 'chat_history'.
        """
        # 1. Extract from CURRENT message
        d_code, d_name, c_name, is_win = self.extract_entities(user_text)

        # 2. CONTEXT FILLING (If missing, look back)
        if not c_name or (not d_code and not is_win):
            # Loop backwards through history (newest first)
            for msg in reversed(chat_history):
                if msg["role"] == "user":
                    past_d_code, past_d_name, past_c_name, _ = self.extract_entities(msg["content"])
                    
                    # Fill gaps if we found something new
                    if not c_name and past_c_name:
                        c_name = past_c_name
                    if not d_code and past_d_code:
                        d_code = past_d_code
                        d_name = past_d_name
                    
                    # Stop if we have everything
                    if c_name and d_code:
                        break

        # 3. EXECUTE LOGIC (With filled context)
        text = user_text.lower()
        if "hello" in text or "hi " in text:
            return random.choice(GREETINGS)
            
        if "pit loss" in text and c_name:
            loss = get_pit_loss(c_name)
            return f"Calculated pit loss for {c_name} is **{loss} seconds**."
            
        # Scenario A: Full Race Prediction
        if is_win and c_name:
            return self.simulate_full_race(c_name)
            
        # Scenario B: Single Driver Strategy
        if d_code and c_name:
            return self.run_single_strategy(d_code, d_name, c_name)
            
        # Scenario C: Still Missing Info
        if is_win and not c_name:
            return "I know you want a race prediction, but I still need the Circuit. (e.g., 'in Bahrain')"
            
        if d_code:
            return f"I have {d_name} selected, but I need a Circuit to run the strategy."
            
        if c_name:
            return f"I have the data for {c_name}. Tell me which Driver to analyze, or ask 'Who will win?'"

        return "Negative. Please specify a Driver and Circuit, or ask for a Race Prediction."

    def run_single_strategy(self, driver_code, driver_name, circuit_name):
        try:
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
            
            for name, code in DRIVERS.items():
                strat, desc, time = solve_scenario(
                    self.model, self.encoder, code, circuit_name, 
                    pit_loss, 1.5, "", "Standard Q3", fast_mode=True
                )
                bias = 0
                if code in ["VER", "HAM", "LEC", "NOR"]: bias = -5
                elif code in ["BOT", "HUL", "OCO"]: bias = +10
                results.append({"Driver": name, "Time": time + bias, "Strategy": strat})
            
            results.sort(key=lambda x: x['Time'])
            winner, p2, p3 = results[0], results[1], results[2]
            
            return f"""
            ### 🏁 Race Prediction: {circuit_name}
            
            **🥇 WINNER:** {winner['Driver']} ({winner['Strategy']})
            **🥈 P2:** {p2['Driver']} (+{(p2['Time'] - winner['Time']):.2f}s)
            **🥉 P3:** {p3['Driver']} (+{(p3['Time'] - winner['Time']):.2f}s)
            """
        except Exception as e:
            return f"Simulation failed: {str(e)}"