import random
import re
import pandas as pd
from src.physics import get_pit_loss
from src.solve_strategy_battle import solve_scenario, load_artifacts

# "Personality" responses
GREETINGS = [
    "Radio check. Loud and clear. How can I help with the strategy?",
    "Pit wall here. I'm ready to run the numbers.",
    "Copy that. I'm online. Ask me about a driver, a full race prediction, or specify custom tyre constraints."
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

    def extract_constraints(self, text):
        """
        Uses Regex to find inventory constraints in natural language.
        e.g., "no new mediums" -> {'compound': 'MEDIUM', 'status': 'NEW', 'limit': 0}
        e.g., "only 1 hard" -> {'compound': 'HARD', 'status': 'NEW', 'limit': 1}
        """
        text = text.lower()
        constraints = []
        
        # Regex Patterns
        # 1. "no new [compound]s"
        pattern_no_new = r"no new (soft|medium|hard)s?"
        matches_no = re.findall(pattern_no_new, text)
        for comp in matches_no:
            constraints.append({'compound': comp.upper(), 'status': 'NEW', 'limit': 0})
            
        # 2. "only [N] new [compound]s" or "does not have [N] new [compound]s"
        # Handles: "only 1 new hard", "does not have 2 new mediums" (implies limit 1)
        pattern_count = r"(only|does not have)\s+(\d+)\s*(new\s+)?(soft|medium|hard)s?"
        matches_count = re.findall(pattern_count, text)
        for modifier, count_str, status_str, comp_str in matches_count:
            count = int(count_str)
            status = 'NEW' if 'new' in status_str else 'USED' # Default to used if not specified, simple logic for now
            compound = comp_str.upper()
            
            limit = count
            if modifier == "does not have":
                 # If they "don't have 2", assume they have 1. If "don't have 1", assume 0.
                 limit = max(0, count - 1)
            
            constraints.append({'compound': compound, 'status': 'NEW', 'limit': limit})
            # Also apply to used just in case user wasn't specific, to be safe
            if 'new' not in status_str:
                 constraints.append({'compound': compound, 'status': 'USED', 'limit': limit})

        return constraints

    def extract_entities(self, text):
        # ... (Keep this function exactly the same as before) ...
        text = text.lower()
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

        driver_code = None
        driver_name = None
        name_map = {"max": "VER", "verstappen": "VER", "lewis": "HAM", "hamilton": "HAM", "lando": "NOR", "norris": "NOR", "charles": "LEC", "leclerc": "LEC", "oscar": "PIA", "piastri": "PIA", "george": "RUS", "russell": "RUS", "kimi": "ANT", "antonelli": "ANT", "fernando": "ALO", "alonso": "ALO", "carlos": "SAI", "sainz": "SAI", "alex": "ALB", "albon": "ALB", "checo": "PER", "perez": "PER", "bottas": "BOT"}
        for name, code in name_map.items():
            if name in text:
                driver_code = code
                driver_name = name.capitalize()
                break

        win_keywords = ["win", "winner", "podium", "predict", "result"]
        is_race_prediction = any(k in text for k in win_keywords)
        return driver_code, driver_name, circuit_name, is_race_prediction

    def analyze_query(self, user_text, chat_history=[]):
        # 1. Extract Entities & CONSTRAINTS from CURRENT message
        d_code, d_name, c_name, is_win = self.extract_entities(user_text)
        constraints = self.extract_constraints(user_text) # <--- NEW NLU STEP

        # 2. CONTEXT FILLING (Look back for missing Drivers/Circuits)
        if not c_name or (not d_code and not is_win):
            for msg in reversed(chat_history):
                if msg["role"] == "user":
                    past_d_code, past_d_name, past_c_name, _ = self.extract_entities(msg["content"])
                    if not c_name and past_c_name: c_name = past_c_name
                    if not d_code and past_d_code:
                        d_code = past_d_code
                        d_name = past_d_name
                    if c_name and d_code: break

        # 3. EXECUTE LOGIC
        text = user_text.lower()
        if "hello" in text or "hi " in text: return random.choice(GREETINGS)
        if "pit loss" in text and c_name:
            loss = get_pit_loss(c_name)
            return f"Calculated pit loss for {c_name} is **{loss} seconds**."
            
        if is_win and c_name: return self.simulate_full_race(c_name)
            
        # --- PASS CONSTRAINTS TO SINGLE STRATEGY ---
        if d_code and c_name:
            return self.run_single_strategy(d_code, d_name, c_name, constraints)
            
        if is_win and not c_name: return "I need a Circuit for the prediction."
        if d_code: return f"I have {d_name}, but need a Circuit."
        if c_name: return f"I have {c_name}. Which Driver, or ask 'Who will win?'"

        return "Negative. Please specify Driver, Circuit, or constraints like 'no new mediums'."

    def run_single_strategy(self, driver_code, driver_name, circuit_name, constraints=[]):
        try:
            # Pass constraints to the solver
            strat, desc, time = solve_scenario(
                self.model, self.encoder, driver_code, circuit_name, 
                get_pit_loss(circuit_name), 1.5, "", "Standard Q3", 
                fast_mode=False, tyre_constraints=constraints # <--- PASSING CONSTRAINTS
            )
            
            constraint_note = ""
            if constraints:
                note_parts = [f"{c['limit']} {c['status'].lower()} {c['compound'].lower()}" for c in constraints]
                constraint_note = f"\n_Note: Accounting for custom constraint: {', '.join(note_parts)}._"

            if strat == "INVALID":
                 return f"**Strategy Error:** {desc} Please enable more tyres."

            m = int(time // 60)
            s = time % 60
            return f"**Strategy for {driver_name} @ {circuit_name}:**\n\nAI recommends: **{strat}**\n* `{desc}`\n* Race Time: {m}m {s:.2f}s{constraint_note}"
        except Exception as e:
            return f"Telemetry Error: {str(e)}"

    def simulate_full_race(self, circuit_name):
        # ... (Keep exactly the same as before, no constraints supported here yet for simplicity) ...
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
            return f"### 🏁 Race Prediction: {circuit_name}\n\n**🥇 WINNER:** {winner['Driver']} ({winner['Strategy']})\n**🥈 P2:** {p2['Driver']} (+{(p2['Time'] - winner['Time']):.2f}s)\n**🥉 P3:** {p3['Driver']} (+{(p3['Time'] - winner['Time']):.2f}s)"
        except Exception as e:
            return f"Simulation failed: {str(e)}"