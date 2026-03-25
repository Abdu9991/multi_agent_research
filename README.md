# Multi-Agent Research API

This project wraps the existing CrewAI workflow in a small Flask API so it can be deployed on Render or run in Docker.

## Endpoints

- `GET /` returns service metadata.
- `GET /health` returns a health check response.
- `GET /ui` serves a browser-based frontend for testing the workflow.
- `GET /runs` returns recent run history and supports `limit`, `status`, and `q` filters.
- `POST /solve` runs the workflow.

Successful `POST /solve` responses use this shape:

```json
{
  "status": "completed",
  "problem": "Calculate the area of a circle with radius 5",
  "result": {
    "text": "The area of the circle with radius 5 is approximately 78.54 square units."
  }
}
```

Example `GET /runs` response shape:

```json
{
  "status": "ok",
  "filters": {
    "limit": 8,
    "status": "completed",
    "q": "circle"
  },
  "runs": [
    {
      "id": 4,
      "timestamp": "2026-03-24T01:24:20.668154+00:00",
      "problem": "Calculate the area of a circle with radius 5",
      "status": "completed",
      "duration_ms": 16739,
      "error": null,
      "result_preview": "The area of the circle is approximately 78.54..."
    }
  ]
}
```

Example request body:

```json
{
  "problem": "Calculate the area of a circle with radius 5"
}
```

## Local setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a local environment file from [.env.example](.env.example) or set the required environment variables directly.

Minimum for an OpenAI-backed deployment:

```powershell
$env:OPENAI_API_KEY="your_api_key"
$env:OPENAI_MODEL="gpt-4o-mini"
```

4. Start the API with either command:

```powershell
python app.py
```

Or:

```powershell
flask run
```

5. Test the API:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:10000/solve -ContentType 'application/json' -Body '{"problem":"Calculate the area of a circle with radius 5"}'
```

Open the browser UI:

```text
http://localhost:10000/ui
```

## Docker

Build the image:

```powershell
docker build -t multi-agent-research .
```

Run the container:

```powershell
docker run --rm -p 10000:10000 -e OPENAI_API_KEY=your_api_key -e OPENAI_MODEL=gpt-4o-mini multi-agent-research
```

## Render deployment

This repository includes [render.yaml](render.yaml), which defines a Docker-based web service.

Required environment variables in Render:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`

Deploy flow:

1. Push the repository to GitHub.
2. Create a new Blueprint or Web Service in Render.
3. Point Render to this repository.
4. Confirm it uses the included Dockerfile.
5. Add the required secret environment variables.
6. Deploy and verify `GET /health`.

## Notes

- The API currently routes every request through `run_math_task` in [main.py](main.py).
- Existing agent and task definitions remain unchanged.
- Run history is persisted locally in `runs.json` and reloaded on startup.# multi_agent_research
# multi_agent_research
