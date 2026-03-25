import os

import uvicorn
from fastapi import FastAPI

from main import run_task

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok", "service": "multi-agent-research"}


@app.post("/solve")
def solve(payload: dict):
    return {"result": run_task(payload["problem"])}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    uvicorn.run(app, host="127.0.0.1", port=port)
