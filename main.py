from crewai import Crew, Process

from tasks import build_tasks
from agents import (
    strategic_planner,
    tool_executor,
    quality_observer,
    reflective_analyst,
)


def run_task(problem: str):
    crew = Crew(
        agents=[
            strategic_planner,
            tool_executor,
            quality_observer,
            reflective_analyst,
        ],
        tasks=build_tasks(problem),
        process=Process.sequential,
        verbose=True,
    )
    return crew.kickoff()


# Backward compatibility for existing app imports.
def run_math_task(problem: str):
    return run_task(problem)
