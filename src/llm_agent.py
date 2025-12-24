import google.generativeai as genai
import json
import os
from src.physics import get_pit_loss
from src.solve_strategy_battle import solve_scenario, load_artifacts # You might need to expose a map in solve_strategy

# --- CONFIG ---
# We need a map to convert "Max" -> "VER" inside the tool
DRIVER_CODE_MAP = {
    "max": "VER", "verstappen": "VER", "lewis": "HAM", "hamilton": "HAM",
    "lando": "NOR", "norris": "NOR", "charles": "LEC", "leclerc": "LEC",
    "oscar": "PIA", "piastri": "PIA", "george": "RUS", "russell": "RUS",
    "fernando": "ALO", "alonso": "ALO", "carlos": "SAI", "sainz": "SAI",
    "checo": "PER", "perez": "PER", "bottas": "BOT", "kimi": "ANT",
    "antonelli": "ANT", "bearman": "BEA", "ollie": "BEA", "lawson": "LAW"
}

# --- THE TOOL (OUR PHYSICS ENGINE) ---
def run_strategy_simulation(driver_name: str, circuit: str, constraints_description: str = ""):
    """
    Calculates the optimal F1 strategy based on physics simulation.
    
    Args:
        driver_name: Name or nickname of the driver (e.g., "Max", "Hamilton").
        circuit: The race track (e.g., "Bahrain", "Monza").
        constraints_description: Optional. Natural language description of tyre limits (e.g., "no new softs", "only 1 hard").
    """
    print(f"🛠️ LLM TOOL CALL: Simulating {driver_name} @ {circuit} (Constraints: {constraints_description})")
    
    # 1. Resolve Driver Code
    code = DRIVER_CODE_MAP.get(driver_name.lower(), "VER") # Default to Max if unknown
    
    # 2. Resolve Circuit
    circuit = circuit.capitalize()
    if "bahrain" in circuit.lower(): circuit = "Sakhir"
    
    # 3. Parse Constraints (We reuse the LLM's description or basic regex logic here if needed, 
    # but for now let's use a simplified parser or pass empty if complex. 
    # To keep it robust, we will map common LLM descriptions to our dict format)
    
    tyre_constraints = []
    desc = constraints_description.lower()
    
    if "no new soft" in desc: tyre_constraints.append({'compound': 'SOFT', 'status': 'NEW', 'limit': 0})
    if "no new medium" in desc: tyre_constraints.append({'compound': 'MEDIUM', 'status': 'NEW', 'limit': 0})
    if "no new hard" in desc: tyre_constraints.append({'compound': 'HARD', 'status': 'NEW', 'limit': 0})
    
    # 4. Run Simulation
    try:
        model, encoder = load_artifacts()
        pit_loss = get_pit_loss(circuit)
        
        strat, desc, time = solve_scenario(
            model, encoder, code, circuit, pit_loss, 1.5, 
            "", "Standard Q3", fast_mode=False, 
            tyre_constraints=tyre_constraints
        )
        
        m = int(time // 60)
        s = time % 60
        
        return {
            "strategy": strat,
            "details": desc,
            "race_time": f"{m}m {s:.2f}s",
            "driver": code,
            "circuit": circuit
        }
    except Exception as e:
        return {"error": str(e)}

# --- THE AGENT CLASS ---
class F1Agent:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        
        # Define the Tool for the LLM
        self.tools = [run_strategy_simulation]
        
        # Initialize Model with Tools
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=self.tools,
            system_instruction="""
            You are a Race Engineer for a Formula 1 team. 
            Your job is to answer strategic questions using the simulation tool provided.
            
            RULES:
            1. ALWAYS use the `run_strategy_simulation` tool when asked about race outcomes, strategy, or tyre usage. Do not guess.
            2. If the user provides constraints (e.g. "he has no softs"), pass that text to the tool.
            3. Be concise, professional, and technical (like a real engineer on the radio).
            4. If the tool returns a strategy, explain it clearly to the user.
            """
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=True)

    def ask(self, user_input):
        try:
            response = self.chat.send_message(user_input)
            return response.text
        except Exception as e:
            return f"Radio Interference (API Error): {str(e)}"