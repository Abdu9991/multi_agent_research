import json
import os
import socket
import time
from datetime import datetime, timezone
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
RUNS_FILE = BASE_DIR / "runs.json"

app = FastAPI(
    title="Multi-Agent Research API",
    description="FastAPI + CrewAI multi-agent workflow with browser UI",
    version="1.0.0",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
SOLVE_TIMEOUT_SECONDS = int(os.getenv("SOLVE_TIMEOUT_SECONDS", "90"))


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class SolveRequest(BaseModel):
    problem: str = Field(..., min_length=1, description="Problem for the multi-agent system")

    model_config = {
        "json_schema_extra": {"example": {"problem": "Calculate the area of a circle with radius 5"}}
    }


class ResultDetail(BaseModel):
    text: str


class SolveResponse(BaseModel):
    result: ResultDetail
    duration_ms: int


class HealthResponse(BaseModel):
    status: str
    service: str


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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    """Browser UI — Jinja2-rendered HTML page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "llm_configured": _llm_configured()},
    )


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "multi-agent-research"}


@app.get("/api", summary="API info")
def api_info():
    return {
        "service": "multi-agent-research",
        "status": "ok",
        "endpoints": ["GET /", "GET /health", "GET /api", "GET /runs", "POST /solve"],
        "ui": "Open / in a browser for the interactive UI",
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
    problem = payload.problem.strip()
    start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        result_text = _run_task_with_timeout(problem, SOLVE_TIMEOUT_SECONDS)

        if _looks_like_failure_result(result_text):
            raise RuntimeError(result_text)

        elapsed_ms = int((time.perf_counter() - start) * 1000)

        _save_run({
            "timestamp": timestamp,
            "problem": problem,
            "status": "completed",
            "duration_ms": elapsed_ms,
            "error": None,
            "result_preview": result_text[:200],
        })

        return {"result": {"text": result_text}, "duration_ms": elapsed_ms}

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
