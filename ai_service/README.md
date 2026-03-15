# AI Service

This directory contains the FastAPI microservice used by the LibraBot UI embedded in the Django app.

## Purpose

The service provides streaming chat responses for library-related questions.

## Endpoints

- `GET /health`
  - Returns: `{"status": "healthy"}`

- `POST /chat/stream`
  - Accepts a JSON payload:

```json
{
  "messages": [
    {"role": "user", "content": "How do I borrow a book?"}
  ]
}
```

  - Streams Server-Sent Events with incremental response chunks.

## Environment Variables

- `DEEPSEEK_API_KEY` (required for real responses)
- `DEEPSEEK_BASE_URL` (optional, for OpenAI-compatible endpoint override)

Copy and edit:

```bash
cp .env_example .env
```

## Local Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Service URL: `http://localhost:8000`

## Docker

The root `docker-compose.yml` runs this service at host port `8001`.

## Integration Notes

- Frontend widget script: `static/js/chatbot.js`
- Widget markup: `templates/components/chatbot.html`
- Django CSP includes `http://localhost:8001` in `CSP_CONNECT_SRC` for local integration.

## Security Note

CORS is currently configured with `allow_origins=["*"]` in `main.py`. Restrict this in production.
