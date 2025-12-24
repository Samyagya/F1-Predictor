import random
from src.physics import get_pit_loss
from src.solve_strategy_battle import solve_scenario, load_artifacts

# "Personality" responses
GREETINGS = [
    "Radio check. Loud and clear. How can I help with the strategy?",
    "Pit wall here. I'm ready to run the numbers.",
    "Copy that. I'm online. What are we looking at for the next race?"
]

UNKNOWN_CMD = [
    "Negative, I didn't copy that. Could you repeat the Driver and Circuit?",
    "I'm not getting that on the telemetry. Please specify a driver (e.g., VER) and track.",
    "Data link unstable. Try asking: 'Predict strategy for Hamilton at Monaco'"
]

class RaceEngineerAI:
    def __init__(self):
        self.model, self.encoder = load_artifacts()

    def analyze_query(self, user_text):
        text = user_text.lower()
        
        # 1. DETECT DRIVER
        driver_code = None
        driver_name = "Unknown"
        
        # Map common nicknames to Codes
        drivers_map = {
            "verstappen": "VER", "max": "VER", "ver": "VER",
            "hamilton": "HAM", "lewis": "HAM", "ham": "HAM",
            "norris": "NOR", "lando": "NOR", "nor": "NOR",
            "leclerc": "LEC", "charles": "LEC", "lec": "LEC",
            "piastri": "PIA", "oscar": "PIA", "pia": "PIA",
            "russell": "RUS", "george": "RUS", "rus": "RUS",
            "alonso": "ALO", "fernando": "ALO", "alo": "ALO",
            "lawson": "LAW", "liam": "LAW",
            "bearman": "BEA", "ollie": "BEA"
        }
        
        for name, code in drivers_map.items():
            if name in text:
                driver_code = code
                driver_name = name.capitalize()
                break
        
        # 2. DETECT CIRCUIT
        circuit_name = None
        circuits = [
            "sakhir", "bahrain", "jeddah", "monaco", "monza", "silverstone", 
            "spa", "suzuka", "vegas", "miami", "austin", "baku"
        ]
        
        for c in circuits:
            if c in text:
                circuit_name = c.capitalize()
                if c == "bahrain": circuit_name = "Sakhir"
                if c == "vegas": circuit_name = "Las Vegas"
                break
                
        # 3. EXECUTE LOGIC
        if "hello" in text or "hi " in text:
            return random.choice(GREETINGS)
            
        if "pit loss" in text and circuit_name:
            loss = get_pit_loss(circuit_name)
            return f"Calculated pit loss for {circuit_name} is **{loss} seconds** (Entry + Stationary + Exit)."
            
        if driver_code and circuit_name:
            # Run the heavy simulation
            return self.run_simulation(driver_code, driver_name, circuit_name)
            
        if driver_code:
            return f"I have {driver_name} on the monitor, but I need a Circuit to run the strategy. (e.g., 'at Monaco')"
            
        if circuit_name:
            return f"I have the data for {circuit_name}, but which Driver are we analyzing?"

        return random.choice(UNKNOWN_CMD)

    def run_simulation(self, driver_code, driver_name, circuit_name):
        try:
            # We assume Q3 (Standard) for chat queries to keep it fast
            strat, desc, time = solve_scenario(
                self.model, self.encoder, driver_code, circuit_name, 
                get_pit_loss(circuit_name), 1.5, "", "Standard Q3"
            )
            
            m = int(time // 60)
            s = time % 60
            
            return f"""
            **Strategy Report for {driver_name} @ {circuit_name}:**
            
            The AI recommends a **{strat}** strategy.
            
            * **Plan:** `{desc}`
            * **Total Race Time:** {m}m {s:.2f}s
            
            _Engineer's Note:_ This assumes they qualified in the Top 10 using Softs.
            """
        except Exception as e:
            return f"Telemetry Error: {str(e)}"