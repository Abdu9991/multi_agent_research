# Design and Evaluation of a Tool-Using Autonomous Multi-Agent AI System for Goal-Directed Problem Solving

A FastAPI + CrewAI research project that evaluates whether structured multi-agent reasoning with tool use improves reliability over a standard single-agent approach.

## Members
- Abdulrazig Mohammed
- Member 1
- Member 2

## Abstract
This project develops and tests an autonomous AI system designed for advanced tool use and structured reasoning. The workflow uses a CrewAI multi-agent framework with a locally hosted or cloud-backed LLM and follows a `Plan → Act → Observe → Reflect` loop to solve tasks such as budgeting, Python data analysis, mathematical calculations, and structured decision-making.

## Research Motivation
The goal is to examine whether planning, tool use, evaluation, and reflection improve:
- task success rate
- reasoning consistency
- error recovery
- efficiency

## Relevant Works
- **ReAct** — reason and act prompting
- **AutoGPT** and **BabyAGI** — autonomous agent architectures
- **Toolformer** — tool-using language models
- **CrewAI** and **LangGraph** — multi-agent orchestration frameworks
- **Ollama** — local LLM deployment for private experimentation

## Features

- **Protected web app** with Firebase-based sign-in and sign-up pages
- **Research dashboard** with live evaluation metrics, runtime chart, and recent activity
- **Fast-path solving** for arithmetic, geometry, budgeting, project planning, and simple data analysis
- **CrewAI agent workflow** built around `Plan → Act → Evaluate → Reflect`
- **REST API** for health checks, metrics, run history, and problem solving

## Deployment

- **Production**: Deployed on [Render](https://multi-agent-research-uktm.onrender.com/)
- **Framework**: FastAPI + Uvicorn
- **Auth UI**: Firebase Email/Password authentication
- **Container**: Dockerfile included for containerized deployment

## Web Routes

| Route | Purpose |
|------|---------|
| `/` | Default sign-in landing page |
| `/signin` | Sign-in page |
| `/signup` | Sign-up page |
| `/app` | Protected dashboard after authentication |

## API Endpoints

### GET /api
Returns service metadata and available endpoints.

**Example response:**
```json
{
  "service": "multi-agent-research",
  "status": "ok",
  "endpoints": ["GET /", "GET /signin", "GET /signup", "GET /app", "GET /health", "GET /api", "GET /runs", "GET /metrics", "POST /solve"],
  "ui": "Open / or /signin to sign in, or /signup to create an account before entering /app",
  "docs": "/docs"
}
```

### GET /health
Health check endpoint.

**Example response:**
```json
{
  "status": "ok",
  "service": "multi-agent-research"
}
```

### GET /runs
Returns recent run history with optional filtering by status or query text.

### GET /metrics
Returns evaluation metrics such as:
- task success rate
- reasoning consistency
- error recovery
- efficiency

### GET /solve
Returns usage help for the solve endpoint.

### POST /solve
Submit a problem to the multi-agent system.

**Request:**
```json
{
  "problem": "Calculate the area of a circle with radius 5"
}
```

**Example response:**
```json
{
  "result": {
    "text": "The area of the circle is 78.53981633974483."
  },
  "duration_ms": 4
}
```

**PowerShell example:**
```powershell
$body = @{ problem = "Calculate the area of a circle with radius 5" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3000/solve `
  -ContentType "application/json" -Body $body
```

---

## Local Setup

### 1. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\Activate.ps1    # Windows PowerShell
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file based on `.env.example`.

**Required for LLM-backed solving:**
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

**Optional for Firebase-authenticated UI:**
```env
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_APP_ID=your_firebase_app_id_here
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id_here
```

### 4. Start the server
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 3000
```

Or:
```bash
python app.py
```

### 5. Open the app
- Browser UI: `http://127.0.0.1:3000/signin`
- API docs: `http://127.0.0.1:3000/docs`
- Health check: `http://127.0.0.1:3000/health`

---

## Multi-Agent Workflow

The system uses four specialized agents:

1. **Planner Agent** — creates a step-by-step strategy
2. **Tool Agent** — executes calculations, Python analysis, and structured reasoning
3. **Evaluator Agent** — validates correctness and consistency
4. **Reflection Agent** — suggests improvements for future tasks

Together, they support a goal-directed reasoning loop designed for reliability and evaluation.

---

## Docker

Build the image:
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

---

## Testing

Run the tests with:
```bash
python -m pytest test_app.py -v
```

If `pytest` is missing locally, reinstall dependencies:
```bash
pip install -r requirements.txt
```

---

## Technical Stack

- **Framework**: FastAPI 0.116.1
- **Server**: Uvicorn 0.35.0
- **Agent orchestration**: CrewAI 1.12.0
- **Validation**: Pydantic 2.11.10
- **Configuration**: `python-dotenv`
- **Templating**: Jinja2
- **Testing**: pytest
- **Container/Hosting**: Docker + Render
