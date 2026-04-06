from crewai import Task
from agents import (
    strategic_planner,
    tool_executor,
    quality_observer,
    reflective_analyst,
)


def build_tasks(problem: str):
    return [
        Task(
            description=(
                f"Create a step-by-step plan for this goal-directed task: {problem}. "
                "Break the problem into manageable actions and identify whether calculation, Python, or data-analysis tools are needed."
            ),
            agent=strategic_planner,
            expected_output="A concise plan with clear steps, tool choices, and intended outcome.",
        ),
        Task(
            description=(
                f"Execute the plan for: {problem}. Use the available tools when useful, solve the task, and present a clear result with brief reasoning."
            ),
            agent=tool_executor,
            expected_output="A practical answer supported by calculations, Python output, or structured reasoning as needed.",
        ),
        Task(
            description=(
                "Evaluate the answer for correctness, reasoning consistency, and completeness. Detect mistakes or risky assumptions and note any corrections."
            ),
            agent=quality_observer,
            expected_output="A validation report confirming correctness or highlighting issues to fix.",
        ),
        Task(
            description=(
                "Reflect on the outcome and suggest how the system could improve reliability, error recovery, or efficiency on similar future tasks."
            ),
            agent=reflective_analyst,
            expected_output="A short reflection describing lessons learned and improvements for the next run.",
        ),
    ]
