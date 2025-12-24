import os
import json
from groq import Groq
from src.physics import get_pit_loss
from src.solve_strategy_battle import solve_scenario, load_artifacts

# --- CONFIG ---
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
    """
    # 1. Resolve Driver Code
    code = DRIVER_CODE_MAP.get(driver_name.lower(), "VER") 
    
    # 2. Resolve Circuit
    circuit = circuit.capitalize()
    if "bahrain" in circuit.lower(): circuit = "Sakhir"
    
    # 3. Parse Constraints 
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
        
        return json.dumps({
            "strategy": strat,
            "details": desc,
            "race_time": f"{m}m {s:.2f}s",
            "driver": code,
            "circuit": circuit
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- THE AGENT CLASS ---
class F1Agent:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        
        # System Prompt to teach Llama 3 how to behave
        self.system_prompt = """
        You are a Race Engineer for a Formula 1 team. 
        You have access to a tool called 'run_strategy_simulation'.
        
        RULES:
        1. If the user asks about strategy, race outcomes, or tyre usage, YOU MUST USE THE TOOL.
        2. Do not guess. Run the simulation.
        3. The tool takes JSON arguments: {"driver_name": "Max", "circuit": "Bahrain", "constraints_description": "..."}
        4. Be concise and technical.
        """

    def ask(self, user_input):
        # 1. First call: Ask LLM what to do
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # Define the tool for Groq
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "run_strategy_simulation",
                    "description": "Calculate optimal F1 strategy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "driver_name": {"type": "string"},
                            "circuit": {"type": "string"},
                            "constraints_description": {"type": "string"}
                        },
                        "required": ["driver_name", "circuit"]
                    }
                }
            }
        ]

        try:
            # CHANGED: Updated model name to the latest version
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # 2. If LLM wants to use the tool, run it
            if tool_calls:
                messages.append(response_message) # Add the intent to history
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "run_strategy_simulation":
                        # RUN OUR PHYSICS CODE
                        tool_response = run_strategy_simulation(
                            driver_name=function_args.get("driver_name"),
                            circuit=function_args.get("circuit"),
                            constraints_description=function_args.get("constraints_description", "")
                        )
                        
                        # Add result to history
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_response,
                        })

                # 3. Second call: Get final answer based on tool result
                # CHANGED: Updated model name here too
                final_response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages
                )
                return final_response.choices[0].message.content
            
            else:
                return response_message.content

        except Exception as e:
            return f"Radio Failure: {str(e)}"