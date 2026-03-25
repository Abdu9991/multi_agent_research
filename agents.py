
import os

from dotenv import load_dotenv
from crewai import Agent, LLM

from tools import (
    calculator_tool,
    python_executor_tool,
    data_analysis_tool,
)

# agents.py - All 4 Agents (FIXED)

# Load environment variables
load_dotenv()

# ---------------------------
# LLM SELECTION (EXPLICIT)
# ---------------------------

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if OLLAMA_BASE_URL and OLLAMA_MODEL:
    llm = LLM(
        model=f"ollama/{OLLAMA_MODEL}",
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE,
    )
    print(f"[LLM] Using Ollama model: {OLLAMA_MODEL}")
elif OPENAI_API_KEY:
    llm = LLM(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=TEMPERATURE,
    )
    print(f"[LLM] Using OpenAI model: {OPENAI_MODEL}")
else:
    raise RuntimeError("No LLM configured. Set either OLLAMA_* or OPENAI_API_KEY.")

# ---------------------------
# AGENTS (ALL USE SAME LLM)
# ---------------------------

strategic_planner = Agent(
    role="Strategic Planner",
    goal="Create step-by-step plans to solve problems",
    backstory="Expert problem solver with 10 years experience",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

tool_executor = Agent(
    role="Tool Executor",
    goal="Execute tasks using tools accurately",
    backstory="Technical specialist in math, programming, and data",
    verbose=True,
    allow_delegation=False,
    tools=[calculator_tool, python_executor_tool, data_analysis_tool],
    llm=llm,
)

quality_observer = Agent(
    role="Quality Observer",
    goal="Validate results and detect errors",
    backstory="Meticulous quality analyst",
    verbose=True,
    allow_delegation=False,
    tools=[calculator_tool],
    llm=llm,
)

reflective_analyst = Agent(
    role="Reflective Analyst",
    goal="Analyze failures and suggest improvements",
    backstory="Expert in error analysis and improvement",
    verbose=True,
    allow_delegation=False,
    llm=llm,
)

print("4 agents loaded successfully with explicit LLM binding!")
