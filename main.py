
# main.py - Run tasks
import ast
import operator
import re
import sys
import time

from crewai import Crew, Process, Task


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _is_connection_error(exc):
    text = str(exc).lower()
    return (
        "failed to connect to openai api" in text
        or "connection error" in text
        or "timeout" in text
        or "timed out" in text
    )


def _is_auth_error(exc):
    text = str(exc).lower()
    return (
        "incorrect api key" in text
        or "invalid api key" in text
        or "authentication" in text
        or "unauthorized" in text
        or "401" in text
    )


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric values are allowed")
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def _fallback_arithmetic(problem):
    # Try to extract a simple arithmetic expression from prompts like "What is 12*12?"
    match = re.search(r"([0-9\s\+\-\*\/%\(\)\.]{3,})", problem)
    if not match:
        return None
    expr = match.group(1).replace("%", "/100")
    expr = re.sub(r"\s+", "", expr)
    if not expr:
        return None
    try:
        result = _safe_eval(ast.parse(expr, mode="eval").body)
    except Exception:
        return None
    return f"Fallback result: {expr} = {result}"


def _fallback(problem):
    return _fallback_arithmetic(problem)


def run_math_task(problem):
    direct_result = _fallback(problem)
    if direct_result:
        return direct_result

    from agents import strategic_planner, tool_executor, quality_observer

    planning_task = Task(
        description=f"Create a short step-by-step plan to solve: {problem}. Return the plan directly without using tools unless necessary.",
        expected_output="Step-by-step plan",
        agent=strategic_planner,
    )

    execution_task = Task(
        description=f"Solve this problem: {problem}. Use the Calculator tool for arithmetic if needed and return the final answer clearly.",
        expected_output="Complete solution with answer",
        agent=tool_executor,
    )

    validation_task = Task(
        description="Validate that the solution is correct and return a concise confirmation.",
        expected_output="Validation result",
        agent=quality_observer,
    )

    crew = Crew(
        agents=[strategic_planner, tool_executor, quality_observer],
        tasks=[planning_task, execution_task, validation_task],
        process=Process.sequential,
        verbose=True,
    )

    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            return crew.kickoff()
        except Exception as exc:
            print(f"[WARN] Attempt {attempt} failed: {exc}")

            if _is_auth_error(exc):
                return (
                    "ERROR: OpenAI API key is invalid or missing.\n"
                    "Check your OPENAI_API_KEY in the environment or .env file."
                )

            if _is_connection_error(exc) and attempt < attempts:
                time.sleep(attempt)
                continue

            fallback = _fallback(problem)
            if fallback:
                return fallback

            raise

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
