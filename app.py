import os
import socket

import uvicorn
from fastapi import FastAPI

from main import run_task

app = FastAPI()


@app.get("/")
def index():
    return {
        "service": "multi-agent-research",
        "status": "ok",
        "endpoints": ["GET /", "GET /health", "GET /solve", "POST /solve"],
        "message": "Use POST /solve with JSON: {\"problem\": \"...\"}",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "multi-agent-research"}


@app.get("/solve")
def solve_help():
    return {
        "status": "method_not_allowed",
        "message": "Use POST /solve with JSON body.",
        "example": {"problem": "Calculate the area of a circle with radius 9"},
    }


@app.post("/solve")
def solve(payload: dict):
    return {"result": run_task(payload["problem"])}


def _first_available_port(start_port: int, max_attempts: int = 20) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No open port found in range {start_port}-{start_port + max_attempts - 1}")


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
    selected_port = _first_available_port(preferred_port, max_attempts)
    if selected_port != preferred_port:
        print(f"Port {preferred_port} is in use. Starting on port {selected_port} instead.")
    uvicorn.run(app, host=host, port=selected_port)
