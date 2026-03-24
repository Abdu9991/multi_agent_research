
# main.py - Run tasks
import sys

from crewai import Crew, Process, Task

def run_math_task(problem):
    from agents import strategic_planner, tool_executor, quality_observer

    planning_task = Task(
        description=f"Create a plan to solve: {problem}",
        expected_output="Step-by-step plan",
        agent=strategic_planner
    )
    
    execution_task = Task(
        description=f"Solve this problem: {problem}. Use Calculator tool.",
        expected_output="Complete solution with answer",
        agent=tool_executor
    )
    
    validation_task = Task(
        description="Validate the solution is correct",
        expected_output="Validation result",
        agent=quality_observer
    )
    
    crew = Crew(
        agents=[strategic_planner, tool_executor, quality_observer],
        tasks=[planning_task, execution_task, validation_task],
        process=Process.sequential,
        verbose=True
    )
    
    result = crew.kickoff()
    return result

if __name__ == "__main__":
    problem = "Calculate the area of a circle with radius 5"
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    
    print(f"\nSolving: {problem}\n")
    result = run_math_task(problem)
    print(f"\n{'='*60}")
    print("FINAL RESULT:")
    print(f"{'='*60}")
    print(result)
