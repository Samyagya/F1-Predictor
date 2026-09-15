# Feature: AI Race Engineer

---

## What This Feature Does

The AI Race Engineer (Tab 3 in app.py) is a conversational chatbot that acts as an intelligent pit wall engineer. The user types natural language questions and the AI:

1. Interprets the question to identify driver, circuit, and constraints
2. Decides whether to call the strategy simulation tool or answer from knowledge
3. If simulation needed: calls `run_strategy_simulation()` which runs the physics engine
4. Returns a concise, technical response with actual race time data

Example queries:
- "What is the best strategy for Hamilton at Silverstone if he has no new soft tyres?"
- "Who will win at Spa?"
- "Compare Verstappen vs Norris at Monaco"

---

## Files Involved

| File | Role |
|---|---|
| `app.py` (Tab 3 block, lines 177-214) | Chat UI, session state management, message rendering |
| `src/llm_agent.py` | F1Agent class, Groq client, tool definition, two-turn call |
| `src/solve_strategy_battle.py` | Called by tool function to run the actual simulation |
| `src/physics.py` | Called by tool function for pit loss |

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM Model | Llama 3.3 70B Versatile (via Groq) |
| Inference Provider | Groq API (groq Python SDK) |
| Tool / Function Calling | Groq function calling with `tool_choice="auto"` |
| Chat UI | Streamlit st.chat_message, st.chat_input, st.status |
| State Management | st.session_state (chat_history list, agent object) |
| Constraint Parsing | Python string matching in llm_agent.py |
| Strategy Simulation | solve_strategy_battle.py (same engine as Tabs 1 and 2) |

---

## Architecture: Two-Turn LLM Pattern

```
User types query
      |
      v
F1Agent.ask(user_input)
      |
      v
CALL 1: Groq API (llama-3.3-70b-versatile)
  - System prompt: "You are a race engineer. Use the tool."
  - User message: the user's query
  - Tools: [run_strategy_simulation]
  - tool_choice: "auto"
      |
      v
Did the LLM decide to call the tool?
  YES                    NO
   |                      |
   v                      v
run_strategy_simulation()  Return LLM content directly
   |
   v
solve_scenario() -> (strategy, desc, time_seconds)
   |
   v
Append tool result to message history
   |
   v
CALL 2: Groq API (llama-3.3-70b-versatile)
  - Now includes: original messages + tool result
  - Generates final human-readable response
   |
   v
Display in chat bubble
```

---

## Tool Definition (Function Calling Schema)

```json
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
```

---

## Tyre Constraint Handling

The tool accepts a plain English `constraints_description` string. Inside `run_strategy_simulation()`, this string is parsed with simple keyword matching:

- "no new soft" -> removes SOFT from all strategy templates
- "no new medium" -> removes MEDIUM from strategy templates  
- "no new hard" -> removes HARD from strategy templates

This parsing logic lives in `llm_agent.py`, not in the LLM prompt — keeping the LLM responsible only for recognising the constraint type, not for parsing the strategy rules.

---

## API Key Management

The Groq API key is managed in order of priority:
1. **Streamlit Secrets** (`st.secrets["GROQ_API_KEY"]`) — used in production (Streamlit Cloud)
2. **Sidebar Input** — user can paste their key directly in the sidebar if no secret is configured

The agent object is stored in `st.session_state["agent"]` so it is not reinitialised on every rerender.

---

## Decisions Made for This Feature

### Why Groq + Llama 3.3 instead of OpenAI + GPT-4?
Groq's inference speed is ~10x faster than OpenAI for the same model size class. For a live chat interface, latency matters. Groq's free tier is also generous enough for development and moderate production traffic. Llama 3.3 70B supports function calling natively, making tool use reliable.

### Why use function calling instead of few-shot prompting for simulation?
Function calling guarantees structured output (JSON arguments) from the LLM. Few-shot prompting would require parsing unstructured text to extract driver/circuit/constraints, which is fragile. Function calling is the industry standard for LLM-tool orchestration.

### Why two separate API calls instead of streaming?
The first call is needed to get the tool call arguments. Only after running the tool and getting results can the second call generate a meaningful response. This is an inherent architectural requirement of the function calling pattern, not a design choice.

### Why is chat history stored in st.session_state but not persisted across sessions?
The app has no user accounts or database. Session state is per-browser-session, which matches the expected use case: a user opens the app, has a conversation, and closes. Persisting history would require a backend (out of scope for Phase 1-6).

### Why does the system prompt say "Do not guess. Run the simulation."?
Without this instruction, the LLM occasionally generates plausible-sounding strategy times from its training data rather than calling the tool. The explicit instruction prevents hallucinated race times.

### Why use ai_analyst.py as a legacy fallback instead of the LLM agent?
`ai_analyst.py` was the original NLU approach using regex pattern matching. It worked without an API key but was less capable. When Groq was integrated, `llm_agent.py` replaced it in `app.py`. `ai_analyst.py` is preserved as reference code and a potential offline fallback.
