
import os
import urllib.request

import litellm
from dotenv import load_dotenv
from crewai import Agent, LLM

try:
    from crewai.llms import Ollama, OpenAI
except ImportError:
    # crewai 1.11.x only exposes the generic LLM class
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

load_dotenv()

TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _ollama_reachable(base_url: str, timeout: float = 3.0) -> bool:
    """Return True only if Ollama responds within *timeout* seconds.
    Prevents a 600-second litellm hang when Ollama is configured but not running."""
    try:
        urllib.request.urlopen(
            f"{base_url.rstrip('/')}/api/version", timeout=timeout
        )
        return True
    except Exception:
        return False


# -------- LLM Selection (Ollama → OpenAI, fail-fast) --------
llm = None
_using_ollama = False  # True when Ollama is active (affects tool-calling support)

if OLLAMA_BASE_URL and OLLAMA_MODEL:
    if _ollama_reachable(OLLAMA_BASE_URL):
        llm = Ollama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=TEMPERATURE)
        _using_ollama = True
        print(f"[LLM] Using Ollama: {OLLAMA_MODEL} @ {OLLAMA_BASE_URL}")
    else:
        print(f"[LLM] Ollama unreachable at {OLLAMA_BASE_URL} — falling back to OpenAI")

if llm is None:
    if OPENAI_API_KEY:
        llm = OpenAI(model=OPENAI_MODEL, temperature=TEMPERATURE)
        print(f"[LLM] Using OpenAI: {OPENAI_MODEL}")
    else:
        raise RuntimeError(
            "No LLM available. Either start Ollama (set OLLAMA_BASE_URL + OLLAMA_MODEL) "
            "or set OPENAI_API_KEY in your .env file."
        )

# Most base Ollama models (llama2, mistral, etc.) don't support the OpenAI tools API.
# When using Ollama, tell LiteLLM to drop unsupported params rather than crash, and
# give agents empty tool lists so no tool-calling payload is ever sent to the model.
if _using_ollama:
    litellm.drop_params = True
    print("[LLM] Ollama mode: tool calling disabled (llm2/mistral don't support tools API)")

# Agents receive tools only when the LLM actually supports function calling.
_tools_enabled = not _using_ollama

# -------- Agents --------
strategic_planner = Agent(
    role="Planner Agent",
    goal="Create step-by-step plans to solve problems",
    backstory="Expert planner",
    llm=llm,
    tools=[reasoning_logger_tool] if _tools_enabled else [],
    verbose=True,
)

tool_executor = Agent(
    role="Tool Agent",
    goal="Execute calculations, coding, and data analysis",
    backstory="Math and programming expert",
    tools=[calculator_tool, python_executor_tool, data_analysis_tool] if _tools_enabled else [],
    llm=llm,
    verbose=True,
)

quality_observer = Agent(
    role="Evaluator Agent",
    goal="Verify correctness of outputs",
    backstory="Quality assurance specialist",
    llm=llm,
    tools=[calculator_tool] if _tools_enabled else [],
    verbose=True,
)

reflective_analyst = Agent(
    role="Reflection Agent",
    goal="Analyze failures and improve future reasoning",
    backstory="Self-improvement analyst",
    llm=llm,
    tools=[reasoning_logger_tool] if _tools_enabled else [],
    verbose=True,
)

print("4 agents loaded successfully")
