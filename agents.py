
# agents.py - All 4 Agents
from crewai import Agent
from tools import calculator_tool, python_executor_tool, data_analysis_tool, reasoning_logger_tool
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

strategic_planner = Agent(
    role="Strategic Planner",
    goal="Create step-by-step plans to solve problems",
    backstory="Expert problem solver with 10 years experience",
    verbose=True,
    allow_delegation=False,
    tools=[reasoning_logger_tool]
)

tool_executor = Agent(
    role="Tool Executor",
    goal="Execute tasks using tools accurately",
    backstory="Technical specialist in math, programming, and data",
    verbose=True,
    allow_delegation=False,
    tools=[calculator_tool, python_executor_tool, data_analysis_tool, reasoning_logger_tool]
)

quality_observer = Agent(
    role="Quality Observer",
    goal="Validate results and detect errors",
    backstory="Meticulous quality analyst",
    verbose=True,
    allow_delegation=False,
    tools=[calculator_tool, reasoning_logger_tool]
)

reflective_analyst = Agent(
    role="Reflective Analyst",
    goal="Analyze failures and suggest improvements",
    backstory="Expert in error analysis and improvement",
    verbose=True,
    allow_delegation=False,
    tools=[reasoning_logger_tool]
)

print("4 agents loaded successfully!")
