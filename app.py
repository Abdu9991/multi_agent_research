import os
import time

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from metrics import get_recent_runs, record_run

load_dotenv()

app = Flask(__name__)


def is_llm_configured():
    return bool(os.getenv("OPENAI_API_KEY"))


def api_error(message, status_code):
    return jsonify({"status": "error", "error": message}), status_code


def format_result(problem, result, duration_ms, run_id):
    result_text = str(result).strip()
    return jsonify(
        {
            "status": "completed",
            "problem": problem,
            "duration_ms": duration_ms,
            "run_id": run_id,
            "result": {"text": result_text},
        }
    )


@app.get("/")
def index():
    return jsonify(
        {
            "service": "multi-agent-research",
            "status": "ok",
            "llm_configured": is_llm_configured(),
            "endpoints": ["GET /", "GET /health", "GET /ui", "GET /runs", "POST /solve"],
            "message": "POST /solve with JSON {\"problem\": \"...\"} to run the CrewAI workflow.",
        }
    )


@app.get("/ui")
def ui():
    return render_template("index.html", llm_configured=is_llm_configured())


@app.get("/health")
def health_check():
    return jsonify({"status": "healthy", "llm_configured": is_llm_configured()})


@app.get("/runs")
def recent_runs():
    limit = request.args.get("limit", default=10, type=int) or 10
    status = request.args.get("status", default=None, type=str)
    query = request.args.get("q", default=None, type=str)
    runs = get_recent_runs(limit=limit, status=status, query=query)
    return jsonify(
        {
            "status": "ok",
            "filters": {"limit": limit, "status": status, "q": query},
            "runs": runs,
        }
    )


@app.post("/solve")
def solve():
    start = time.perf_counter()
    payload = request.get_json(silent=True) or {}
    problem = (payload.get("problem") or "").strip()

    if not problem:
        duration_ms = int((time.perf_counter() - start) * 1000)
        record_run(problem="", status="invalid_request", duration_ms=duration_ms, error="Missing problem")
        return api_error("Request JSON must include a non-empty 'problem' field.", 400)

    if not is_llm_configured():
        duration_ms = int((time.perf_counter() - start) * 1000)
        record_run(problem=problem, status="blocked", duration_ms=duration_ms, error="OPENAI_API_KEY is not configured")
        return api_error("OPENAI_API_KEY is not configured.", 503)

    try:
        from main import run_math_task

        result = run_math_task(problem)
        duration_ms = int((time.perf_counter() - start) * 1000)
        run = record_run(
            problem=problem,
            status="completed",
            duration_ms=duration_ms,
            result_text=str(result),
        )
        return format_result(problem, result, duration_ms=duration_ms, run_id=run["id"])
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        record_run(problem=problem, status="failed", duration_ms=duration_ms, error=str(exc))
        return api_error(str(exc), 500)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)