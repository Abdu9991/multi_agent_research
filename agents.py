
import os

from dotenv import load_dotenv
from crewai import Agent, LLM

try:
    from crewai.llms import Ollama, OpenAI
except ImportError:
    # CrewAI 1.11.x may expose only the generic LLM class.
    class Ollama:  # type: ignore[no-redef]
        def __new__(cls, base_url: str, model: str, temperature: float = 0.7):
            return LLM(
                model=f"ollama/{model}",
                base_url=base_url,
                temperature=temperature,
            )

    class OpenAI:  # type: ignore[no-redef]
        def __new__(cls, model: str, temperature: float = 0.7):
            return LLM(
                model=model,
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=temperature,
            )

from tools import (
    calculator_tool,
    python_executor_tool,
    data_analysis_tool,
    reasoning_logger_tool,
)

# agents.py

load_dotenv()

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# -------- LLM Selection --------
if OLLAMA_BASE_URL and OLLAMA_MODEL:
    llm = Ollama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=TEMPERATURE,
    )
    print(f"[LLM] Using Ollama: {OLLAMA_MODEL}")
elif OPENAI_API_KEY:
    llm = OpenAI(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
    )
    print(f"[LLM] Using OpenAI: {OPENAI_MODEL}")
else:
    raise RuntimeError("No LLM configured")

# -------- Agents --------
strategic_planner = Agent(
    role="Planner Agent",
    goal="Create step-by-step plans to solve problems",
    backstory="Expert planner",
    llm=llm,
    tools=[reasoning_logger_tool],
    verbose=True,
)

tool_executor = Agent(
    role="Tool Agent",
    goal="Execute calculations, coding, and data analysis",
    backstory="Math and programming expert",
    tools=[calculator_tool, python_executor_tool, data_analysis_tool],
    llm=llm,
    verbose=True,
)

quality_observer = Agent(
    role="Evaluator Agent",
    goal="Verify correctness of outputs",
    backstory="Quality assurance specialist",
    llm=llm,
    tools=[calculator_tool],
    verbose=True,
)

reflective_analyst = Agent(
    role="Reflection Agent",
    goal="Analyze failures and improve future reasoning",
    backstory="Self-improvement analyst",
    llm=llm,
    tools=[reasoning_logger_tool],
    verbose=True,
)

print("4 agents loaded successfully")
