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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
