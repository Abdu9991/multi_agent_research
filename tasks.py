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
        ),
        Task(
            description=f"Solve the problem using tools: {problem}",
            agent=tool_executor,
        ),
        Task(
            description="Evaluate the solution for correctness",
            agent=quality_observer,
        ),
        Task(
            description="Reflect on errors and suggest improvements if needed",
            agent=reflective_analyst,
        ),
    ]
