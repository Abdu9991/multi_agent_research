# Multi-Agent Research API

A FastAPI-based service wrapping a CrewAI multi-agent workflow. The system uses four specialized agents (strategic planner, tool executor, quality observer, and reflective analyst) to solve complex problems through collaborative reasoning.

## Deployment

- **Production**: Deployed on [Render](https://multi-agent-research-uktm.onrender.com/)
- **Docker**: Containerized with non-root user execution and ASGI workers
- **Framework**: FastAPI 0.116.1 with Uvicorn

## API Endpoints

### GET /

Service metadata and available endpoints.

**Response** (200 OK):
```json
{
  "service": "multi-agent-research",
  "status": "ok",
  "endpoints": ["GET /", "GET /health", "GET /solve", "POST /solve"],
  "message": "Use POST /solve with JSON: {\"problem\": \"...\"}"
}
```

**cURL example**:
```bash
curl -X GET http://localhost:3000/
```

---

### GET /health

Health check endpoint for monitoring and load balancers.

**Response** (200 OK):
```json
{
  "status": "ok",
  "service": "multi-agent-research"
}
```

**cURL example**:
```bash
curl -X GET http://localhost:3000/health
```

---

### GET /solve

Method information (POST is the supported method).

**Response** (200 OK):
```json
{
  "status": "method_not_allowed",
  "message": "Use POST /solve with JSON body.",
  "example": {
    "problem": "Calculate the area of a circle with radius 9"
  }
}
```

**cURL example**:
```bash
curl -X GET http://localhost:3000/solve
```

---

### POST /solve

Submit a problem to the multi-agent system for solving.

**Request** (Content-Type: application/json):
```json
{
  "problem": "Calculate the area of a circle with radius 5"
}
```

**Request Fields**:
- `problem` (string, required): The problem or task description. Must be non-empty.

**Response** (200 OK):
```json
{
  "result": "The area of the circle with radius 5 is approximately 78.54 square units."
}
```

**Error Responses**:

| Status | Description | Example |
|--------|-------------|---------|
| 400 | Invalid request (missing or empty `problem` field) | `{"detail": "'problem' must be a non-empty string"}` |
| 422 | Validation error (malformed JSON) | `{"detail": [...]}` |
| 503 | Service unavailable (LLM environment not configured) | `{"detail": "Solve unavailable: ..."}` |

**cURL examples**:

Basic request:
```bash
curl -X POST http://localhost:3000/solve \
  -H "Content-Type: application/json" \
  -d '{"problem":"Calculate the area of a circle with radius 5"}'
```

Using jq to format output:
```bash
curl -X POST http://localhost:3000/solve \
  -H "Content-Type: application/json" \
  -d '{"problem":"What is 2+2?"}' | jq .
```

Using PowerShell:
```powershell
$body = @{"problem"="Calculate the area of a circle with radius 5"} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:3000/solve `
  -ContentType 'application/json' -Body $body
```

---

## Local Setup

### 1. Environment

Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 2. Dependencies

Install requirements:
```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Set required OpenAI configuration:
```bash
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-4o-mini"
```

Or on Windows PowerShell:
```powershell
$env:OPENAI_API_KEY = "your_api_key_here"
$env:OPENAI_MODEL = "gpt-4o-mini"
```

### 4. Start the Server

Run with Uvicorn directly:
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 3000
```

Or with the custom app launcher:
```bash
python app.py
```

The server starts on `http://localhost:3000` by default, or the first available port if 3000 is in use.

### 5. Test the API

Request the solve endpoint:
```bash
curl -X POST http://localhost:3000/solve \
  -H "Content-Type: application/json" \
  -d '{"problem":"Explain quantum computing in simple terms"}'
```

Access API documentation (auto-generated):
```
http://localhost:3000/docs          # Swagger UI
http://localhost:3000/redoc         # ReDoc
```

---

## Docker

Build the Docker image:
```bash
docker build -t multi-agent-research .
```

Run the container:
```bash
docker run -e OPENAI_API_KEY="your_key" \
           -e OPENAI_MODEL="gpt-4o-mini" \
           -p 3000:10000 \
           multi-agent-research
```

The container runs on port 10000 internally (mapped to 3000 above).

---

## Multi-Agent System

The system uses four specialized agents that collaborate:

1. **Strategic Planner**: Creates a concise step-by-step plan to solve the problem
2. **Tool Executor**: Computes a final answer with supporting steps
3. **Quality Observer**: Validates correctness and identifies any issues
4. **Reflective Analyst**: Provides reflections and improvement suggestions

Each agent contributes unique expertise through the CrewAI framework, ensuring thorough problem analysis and high-quality solutions.

---

## Testing

Run the test suite:
```bash
pytest test_app.py -v
```

Test coverage includes:
- GET / (service metadata)
- GET /health (health check)
- GET /solve (method not allowed)
- POST /solve (problem solving with valid/invalid inputs)

---

## Deployment

### Render

This repository includes [render.yaml](render.yaml), which defines a Docker-based web service.

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `OPENAI_MODEL` - Model to use (e.g., `gpt-4o-mini`)

Deployment steps:
1. Push to GitHub
2. Create a new Render web service from this repository
3. Confirm Dockerfile is selected
4. Add the required environment variables
5. Deploy and verify with `GET /health`

---

## Technical Stack

- **Framework**: FastAPI 0.116.1
- **Server**: Uvicorn 0.35.0 (ASGI)
- **Multi-Agent**: CrewAI 1.11.0
- **LLM**: OpenAI API (configurable model)
- **Validation**: Pydantic v2
- **Testing**: pytest
- **Container**: Docker with Python 3.12-slim
- **Production**: Render (non-root execution)
