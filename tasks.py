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
            description=f"Create a plan to solve: {problem}",
            agent=strategic_planner,
            expected_output="A concise step-by-step plan to solve the problem.",
        ),
        Task(
            description=f"Solve the problem using tools: {problem}",
            agent=tool_executor,
            expected_output="A computed final answer with brief supporting steps.",
        ),
        Task(
            description="Evaluate the solution for correctness",
            agent=quality_observer,
            expected_output="A validation note confirming correctness or identifying issues.",
        ),
        Task(
            description="Reflect on errors and suggest improvements if needed",
            agent=reflective_analyst,
            expected_output="A short reflection with improvement suggestions.",
        ),
    ]
