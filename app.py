import json
import math
import os
import re
import socket
import statistics
import time
from datetime import datetime, timezone
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from metrics import evaluate
from tools import CalculatorTool  # pre-load crewai at startup so first /solve is fast

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
RUNS_FILE = BASE_DIR / "runs.json"
load_dotenv(BASE_DIR / ".env")

app = FastAPI(
    title="Tool-Using Autonomous Multi-Agent Research System",
    description="CrewAI-based multi-agent problem solving with planning, tool use, evaluation, and reflection.",
    version="1.0.0",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
SOLVE_TIMEOUT_SECONDS = int(os.getenv("SOLVE_TIMEOUT_SECONDS", "300"))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SolveRequest(BaseModel):
    problem: str = Field(..., min_length=1, description="Problem for the multi-agent system")

    @field_validator("problem")
    @classmethod
    def validate_problem(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("problem must not be empty")
        return cleaned

    model_config = {
        "json_schema_extra": {"example": {"problem": "Calculate the area of a circle with radius 5"}}
    }


class IndexResponse(BaseModel):
    service: str
    status: str
    endpoints: list[str]
    message: str


class ResultDetail(BaseModel):
    text: str


class SolveResponse(BaseModel):
    result: ResultDetail
    duration_ms: int


class HealthResponse(BaseModel):
    status: str
    service: str


class MetricsResponse(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    task_success_rate: str
    reasoning_consistency: str
    error_recovery: str
    efficiency: str


# ---------------------------------------------------------------------------
# Runs persistence helpers
# ---------------------------------------------------------------------------

def _load_runs() -> list:
    try:
        return json.loads(RUNS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_run(entry: dict) -> None:
    runs = _load_runs()
    next_id = max((r.get("id", 0) for r in runs), default=0) + 1
    entry["id"] = next_id
    runs.append(entry)
    RUNS_FILE.write_text(json.dumps(runs, indent=2), encoding="utf-8")


def _solve_worker(problem: str, queue: Queue) -> None:
    try:
        from main import run_task

        queue.put({"ok": True, "value": str(run_task(problem))})
    except Exception as exc:  # pragma: no cover - runtime safety boundary
        queue.put({"ok": False, "value": str(exc)})


def _run_task_with_timeout(problem: str, timeout_seconds: int) -> str:
    queue: Queue = Queue()
    process = Process(target=_solve_worker, args=(problem, queue))
    process.start()
    process.join(timeout=timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join(timeout=2)
        raise TimeoutError(f"Timed out after {timeout_seconds} seconds")

    if queue.empty():
        raise RuntimeError("Solve worker exited without a response")

    payload = queue.get()
    if payload.get("ok"):
        return payload.get("value", "")
    raise RuntimeError(payload.get("value", "Unknown solve worker error"))


# ---------------------------------------------------------------------------
# Fast-path shortcuts (bypass the LLM for arithmetic, geometry, and simple budgets)
# ---------------------------------------------------------------------------

# Matches pure arithmetic / math function expressions
_MATH_EXPR_RE = re.compile(
    r'^[\d\s+\-*/().%^,]+$'
    r'|^(sqrt|sin|cos|tan|log|abs|round|circle_area|circle_circumference|circle_radius_from_area|'
    r'circle_radius_from_circumference|square_area|square_perimeter|rectangle_area|rectangle_perimeter|'
    r'triangle_area|sphere_volume|sphere_surface_area|sphere_radius_from_volume|cylinder_volume|'
    r'cylinder_surface_area|cone_volume)\s*\(',
    re.IGNORECASE,
)

# Natural-language geometry patterns -> formula lambda
_NL_MATH_PATTERNS: list = [
    # circle calculations
    (re.compile(r'area\s+of\s+(?:a\s+)?circle.*?radius\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: math.pi * float(m.group(1)) ** 2),
    (re.compile(r'area\s+of\s+(?:a\s+)?circle.*?diameter\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: math.pi * (float(m.group(1)) / 2) ** 2),
    (re.compile(r'(?:circumference|perimeter)\s+of\s+(?:a\s+)?circle.*?radius\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 2 * math.pi * float(m.group(1))),
    (re.compile(r'(?:circumference|perimeter)\s+of\s+(?:a\s+)?circle.*?diameter\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: math.pi * float(m.group(1))),
    (re.compile(r'(?:radius\s+of\s+(?:a\s+)?circle.*?area|find\s+the\s+radius.*?circle.*?area).*?([\d.]+)', re.I),
     lambda m: math.sqrt(float(m.group(1)) / math.pi)),
    (re.compile(r'(?:radius\s+of\s+(?:a\s+)?circle.*?(?:circumference|perimeter)|find\s+the\s+radius.*?(?:circumference|perimeter)).*?([\d.]+)', re.I),
     lambda m: float(m.group(1)) / (2 * math.pi)),
    (re.compile(r'diameter\s+of\s+(?:a\s+)?circle.*?radius\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 2 * float(m.group(1))),

    # 2D shapes
    (re.compile(r'area\s+of\s+(?:a\s+)?square.*?(?:side|length)\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: float(m.group(1)) ** 2),
    (re.compile(r'(?:perimeter)\s+of\s+(?:a\s+)?square.*?(?:side|length)\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 4 * float(m.group(1))),
    (re.compile(r'area\s+of\s+(?:a\s+)?rectangle.*?([\d.]+)\s*(?:by|x|\*|,)\s*([\d.]+)', re.I),
     lambda m: float(m.group(1)) * float(m.group(2))),
    (re.compile(r'area\s+of\s+(?:a\s+)?rectangle.*?(?:width|length)\s*[=:]?\s*([\d.]+).*?(?:height|width|length)\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: float(m.group(1)) * float(m.group(2))),
    (re.compile(r'perimeter\s+of\s+(?:a\s+)?rectangle.*?(?:width|length)\s*[=:]?\s*([\d.]+).*?(?:height|width|length)\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 2 * (float(m.group(1)) + float(m.group(2)))),
    (re.compile(r'area\s+of\s+(?:a\s+)?triangle.*?base\s*[=:]?\s*([\d.]+).*?height\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 0.5 * float(m.group(1)) * float(m.group(2))),
    (re.compile(r'hypotenuse.*?([\d.]+).*?([\d.]+)', re.I),
     lambda m: math.sqrt(float(m.group(1)) ** 2 + float(m.group(2)) ** 2)),

    # 3D shapes
    (re.compile(r'volume\s+of\s+(?:a\s+)?sphere.*?radius\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: (4 / 3) * math.pi * float(m.group(1)) ** 3),
    (re.compile(r'surface\s+area\s+of\s+(?:a\s+)?sphere.*?radius\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 4 * math.pi * float(m.group(1)) ** 2),
    (re.compile(r'radius\s+of\s+(?:a\s+)?sphere.*?volume\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: ((3 * float(m.group(1))) / (4 * math.pi)) ** (1 / 3)),
    (re.compile(r'volume\s+of\s+(?:a\s+)?cylinder.*?radius\s*[=:]?\s*([\d.]+).*?height\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: math.pi * float(m.group(1)) ** 2 * float(m.group(2))),
    (re.compile(r'surface\s+area\s+of\s+(?:a\s+)?cylinder.*?radius\s*[=:]?\s*([\d.]+).*?height\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: 2 * math.pi * float(m.group(1)) * (float(m.group(1)) + float(m.group(2)))),
    (re.compile(r'volume\s+of\s+(?:a\s+)?cone.*?radius\s*[=:]?\s*([\d.]+).*?height\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: (math.pi * float(m.group(1)) ** 2 * float(m.group(2))) / 3),
    (re.compile(r'volume\s+of\s+(?:a\s+)?cube.*?(?:side|edge|length)\s*[=:]?\s*([\d.]+)', re.I),
     lambda m: float(m.group(1)) ** 3),
]


def _fmt(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.6f}".rstrip('0').rstrip('.')


def _currency(value: float) -> str:
    return f"${value:,.2f}"


def _try_budget_plan(problem: str) -> Optional[str]:
    normalized = problem.lower()
    if "budget" not in normalized or "income" not in normalized:
        return None

    amount_pattern = re.compile(
        r"\b(income|rent|food|transport(?:ation)?|utilities|books?|phone|internet|misc(?:ellaneous)?|"
        r"entertainment|savings?\s+goal)\b\s*(?:of|is|=|:|at|with)?\s*\$?\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )

    income = None
    savings_goal = 0.0
    expenses: dict[str, float] = {}

    for raw_label, raw_amount in amount_pattern.findall(problem):
        label = raw_label.lower().strip()
        amount = float(raw_amount)

        if label == "income":
            income = amount
        elif "savings" in label:
            savings_goal = amount
        else:
            key = "transport" if label.startswith("transport") else label.rstrip("s")
            expenses[key] = amount

    if income is None:
        return None

    total_expenses = sum(expenses.values())
    remaining_after_expenses = income - total_expenses
    remaining_after_savings = remaining_after_expenses - savings_goal

    expense_lines = "\n".join(
        f"- {name.replace('_', ' ').title()}: {_currency(amount)}"
        for name, amount in expenses.items()
    ) or "- No expenses provided"

    if remaining_after_savings >= 0:
        summary = f"You can meet the savings goal and still have {_currency(remaining_after_savings)} left."
    else:
        summary = f"You are short by {_currency(abs(remaining_after_savings))} after the savings goal."

    return (
        "Monthly student budget summary\n"
        f"Income: {_currency(income)}\n"
        "Expenses:\n"
        f"{expense_lines}\n"
        f"Total expenses: {_currency(total_expenses)}\n"
        f"Savings goal: {_currency(savings_goal)}\n"
        f"Remaining after expenses: {_currency(remaining_after_expenses)}\n"
        f"Result: {summary}"
    )


def _try_project_schedule(problem: str) -> Optional[str]:
    normalized = problem.lower()
    if "phase" not in normalized or "day" not in normalized:
        return None
    if not any(keyword in normalized for keyword in ["order", "efficient", "schedule", "sequence"]):
        return None

    duration_match = re.search(r"with\s+([\d\s,and]+)\s+days", normalized)
    if not duration_match:
        return None

    values = [int(value) for value in re.findall(r"\d+", duration_match.group(1))]
    if len(values) < 2:
        return None

    phases = [(index + 1, days) for index, days in enumerate(values)]
    recommended_order = sorted(phases, key=lambda item: (item[1], item[0]))
    ordered_labels = " -> ".join(f"Phase {index} ({days} days)" for index, days in recommended_order)
    total_days = sum(days for _, days in phases)

    return (
        "Recommended project order\n"
        f"Order: {ordered_labels}\n"
        f"Total project time: {total_days} days\n"
        "Why: assuming the phases are independent, starting with the shortest phase first creates early progress, "
        "delivers quick feedback, and reduces the risk of spending too long on the biggest phase before seeing results."
    )


def _try_data_analysis(problem: str) -> Optional[str]:
    normalized = problem.lower()
    if not any(keyword in normalized for keyword in ["analyze", "analysis", "mean", "median", "spread", "statistics"]):
        return None

    data_match = re.search(r"numbers?\s+(.+?)(?:\s+and\s+summarize|\s+using\s+python|$)", problem, re.IGNORECASE)
    candidate_text = data_match.group(1) if data_match else problem
    values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", candidate_text)]

    if len(values) < 2:
        return None

    mean_value = statistics.mean(values)
    median_value = statistics.median(values)
    range_value = max(values) - min(values)
    stdev_value = statistics.stdev(values) if len(values) > 1 else 0.0
    formatted_values = ", ".join(_fmt(value) for value in values)

    return (
        "Python data analysis summary\n"
        f"Data: {formatted_values}\n"
        f"Mean: {_fmt(mean_value)}\n"
        f"Median: {_fmt(median_value)}\n"
        f"Spread (range): {_fmt(range_value)}\n"
        f"Min/Max: {_fmt(min(values))} / {_fmt(max(values))}\n"
        f"Standard deviation: {_fmt(stdev_value)}"
    )


def _friendly_result_text(problem: str, result_text: str) -> str:
    cleaned = str(result_text).strip()
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", cleaned):
        return cleaned

    normalized = problem.lower()
    metric = "answer"
    if "surface area" in normalized:
        metric = "surface area"
    elif "area" in normalized:
        metric = "area"
    elif "circumference" in normalized:
        metric = "circumference"
    elif "perimeter" in normalized:
        metric = "perimeter"
    elif "radius" in normalized:
        metric = "radius"
    elif "diameter" in normalized:
        metric = "diameter"
    elif "volume" in normalized:
        metric = "volume"
    elif "hypotenuse" in normalized:
        metric = "hypotenuse"

    shape = ""
    for candidate in ["circle", "square", "rectangle", "triangle", "sphere", "cylinder", "cone", "cube"]:
        if candidate in normalized:
            shape = candidate
            break

    if shape:
        return f"The {metric} of the {shape} is {cleaned}."
    return f"The {metric} is {cleaned}."


def _try_calculator(problem: str) -> Optional[str]:
    """Return an instant result for pure arithmetic, common geometry phrases,
    or simple budget prompts; otherwise fall through to the CrewAI workflow."""
    expr = problem.strip()

    budget_result = _try_budget_plan(expr)
    if budget_result is not None:
        return budget_result

    project_result = _try_project_schedule(expr)
    if project_result is not None:
        return project_result

    analysis_result = _try_data_analysis(expr)
    if analysis_result is not None:
        return analysis_result

    # 1. Pure arithmetic / math function
    if _MATH_EXPR_RE.match(expr):
        result = CalculatorTool()._run(expr)
        if not result.startswith("Error:"):
            return result

    # 2. Natural-language geometry / formula phrases
    for pattern, formula in _NL_MATH_PATTERNS:
        m = pattern.search(expr)
        if m:
            try:
                return _fmt(formula(m))
            except Exception:
                continue  # bad numbers — fall through to LLM

    return None


def _looks_like_failure_result(result_text: str) -> bool:
    normalized = result_text.strip().lower()
    failure_markers = [
        "error:",
        "invalid api key",
        "openai api key is invalid",
        "timeout",
        "apiconnectionerror",
        "cannot import name",
    ]
    return any(marker in normalized for marker in failure_markers)


# ---------------------------------------------------------------------------
# LLM detection helper (for template context)
# ---------------------------------------------------------------------------

def _llm_configured() -> bool:
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_ollama = bool(os.getenv("OLLAMA_BASE_URL") and os.getenv("OLLAMA_MODEL"))
    return has_openai or has_ollama


def _firebase_public_config() -> dict[str, str]:
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY", ""),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": os.getenv("FIREBASE_APP_ID", ""),
    }


def _firebase_enabled() -> bool:
    config = _firebase_public_config()
    required_keys = ["apiKey", "authDomain", "projectId", "appId"]
    placeholder_markers = ("your_", "example", "replace_me", "paste_")

    for key in required_keys:
        value = (config.get(key) or "").strip().lower()
        if not value or any(marker in value for marker in placeholder_markers):
            return False

    return True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _template_context(request: Request) -> dict:
    return {
        "request": request,
        "llm_configured": _llm_configured(),
        "evaluation_metrics": evaluate(_load_runs()),
        "firebase_enabled": _firebase_enabled(),
        "firebase_config_json": json.dumps(_firebase_public_config()),
    }


def _has_app_access(request: Request) -> bool:
    return (
        request.cookies.get("app_access") == "1"
        and request.cookies.get("auth_mode") == "firebase"
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page(request: Request):
    """Firebase sign-in landing page."""
    if _has_app_access(request):
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse("signin.html", _template_context(request))


@app.get("/signin", response_class=HTMLResponse, include_in_schema=False)
def signin_page(request: Request):
    if _has_app_access(request):
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse("signin.html", _template_context(request))


@app.get("/signup", response_class=HTMLResponse, include_in_schema=False)
def signup_page(request: Request):
    if _has_app_access(request):
        return RedirectResponse(url="/app", status_code=303)
    return templates.TemplateResponse("signup.html", _template_context(request))


@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
def app_page(request: Request):
    """Main browser UI after sign-in."""
    if not _has_app_access(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("index.html", _template_context(request))


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "multi-agent-research"}


@app.get("/api", summary="API info")
def api_info():
    return {
        "service": "multi-agent-research",
        "status": "ok",
        "endpoints": ["GET /", "GET /signin", "GET /signup", "GET /app", "GET /health", "GET /api", "GET /runs", "GET /metrics", "POST /solve"],
        "ui": "Open / or /signin to sign in, or /signup to create an account before entering /app",
        "docs": "/docs",
    }


@app.get("/runs", summary="Run history")
def get_runs(
    limit: int = Query(default=8, ge=1, le=100),
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
):
    runs = _load_runs()
    if status:
        runs = [r for r in runs if r.get("status") == status]
    if q:
        q_lower = q.lower()
        runs = [
            r for r in runs
            if q_lower in (r.get("problem") or "").lower()
            or q_lower in (r.get("result_preview") or "").lower()
        ]
    # Return most-recent first, up to limit
    return {"runs": list(reversed(runs))[:limit]}


@app.get("/metrics", response_model=MetricsResponse, summary="Evaluation metrics")
def get_metrics():
    return evaluate(_load_runs())


@app.get("/solve", summary="Solve help (GET)")
def solve_help():
    return {
        "status": "method_not_allowed",
        "message": "Use POST /solve with a JSON body.",
        "example": {"problem": "Calculate the area of a circle with radius 9"},
    }


@app.post("/solve", response_model=SolveResponse, summary="Run multi-agent workflow")
def solve(payload: SolveRequest):
    """Submit a problem to the 4-agent CrewAI workflow and get the result."""
    problem = payload.problem
    start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    # --- Fast path: pure arithmetic → no LLM needed ---
    quick_result = _try_calculator(problem)
    if quick_result is not None:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        friendly_text = _friendly_result_text(problem, quick_result)
        _save_run({
            "timestamp": timestamp,
            "problem": problem,
            "status": "completed",
            "duration_ms": elapsed_ms,
            "error": None,
            "result_preview": friendly_text[:200],
        })
        return {"result": {"text": friendly_text}, "duration_ms": elapsed_ms}

    try:
        result_text = _run_task_with_timeout(problem, SOLVE_TIMEOUT_SECONDS)

        if _looks_like_failure_result(result_text):
            raise RuntimeError(result_text)

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        friendly_text = _friendly_result_text(problem, result_text)

        _save_run({
            "timestamp": timestamp,
            "problem": problem,
            "status": "completed",
            "duration_ms": elapsed_ms,
            "error": None,
            "result_preview": friendly_text[:200],
        })

        return {"result": {"text": friendly_text}, "duration_ms": elapsed_ms}

    except TimeoutError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        error_msg = (
            f"Solve timed out after {SOLVE_TIMEOUT_SECONDS} seconds. "
            "If Ollama is configured, verify it is reachable and responsive."
        )

        _save_run({
            "timestamp": timestamp,
            "problem": problem,
            "status": "failed",
            "duration_ms": elapsed_ms,
            "error": error_msg,
            "result_preview": "",
        })

        raise HTTPException(status_code=504, detail=error_msg) from exc

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        error_msg = str(exc)

        _save_run({
            "timestamp": timestamp,
            "problem": problem,
            "status": "failed",
            "duration_ms": elapsed_ms,
            "error": error_msg,
            "result_preview": "",
        })

        raise HTTPException(status_code=503, detail=f"Solve unavailable: {error_msg}") from exc


# ---------------------------------------------------------------------------
# Dev server entry-point
# ---------------------------------------------------------------------------

def _first_available_port(host: str, start_port: int, max_attempts: int = 20) -> int:
    bind_host = "0.0.0.0" if host in {"", "0.0.0.0"} else host
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((bind_host, port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No open port found in range {start_port}–{start_port + max_attempts - 1}")


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    preferred_port = _int_env("PORT", 3000)
    max_attempts = max(1, _int_env("PORT_SCAN_ATTEMPTS", 20))
    selected_port = _first_available_port(host, preferred_port, max_attempts)
    if selected_port != preferred_port:
        print(f"Port {preferred_port} in use — starting on port {selected_port} instead.")
    print(f"  UI  → http://localhost:{selected_port}/")
    print(f"  API → http://localhost:{selected_port}/docs")
    uvicorn.run(app, host=host, port=selected_port)
