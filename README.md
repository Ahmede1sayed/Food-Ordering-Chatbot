# Primos Chatbot

Pizza restaurant chatbot and ordering API (Python + FastAPI)

This repository provides a conversational ordering chatbot (Primos) with routes, database migrations, and LLM provider interfaces. It includes services for cart management, menu browsing, and an LLM integration layer.

## Features
- FastAPI-based API with chat endpoints
- Database migrations via Alembic
- LLM provider abstraction (Groq, OpenAI)
- Menu, cart and order services

## Requirements
- Python 3.10+ (or compatible)
- A running database (MySQL / MariaDB compatible) referenced in `.env`

Install dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Environment
Copy the example env and fill values:

```bash
cp app/.env.example app/.env
```

app/.env.example contains:

```
DB_NAME="YOUR_DB_NAME"
DB_USER="YOUR_DB_USER"
DB_PASSWORD="YOUR_DB_PASSWORD"
DB_HOST="127.0.0.1"
DB_PORT=3307
DEFAULT_LANG="en"
GROQ_API_KEY="YOUR_GROQ_API_KEY"
LLM_PROVIDER="groq"
LLM_MODEL="llama-3.3-70b-versatile"
LLM_TEMPERATURE=0.1
```

Adjust `DB_PORT` and other values as needed.

## Database migrations
This project uses Alembic. Configure the DB connection in `app/database/connection.py` or via env vars, then:

```bash
alembic upgrade head
```

## Running (development)
Start the FastAPI app with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `GET /health`

Chat API: the chat router is mounted at `/api` (see `app/routes/chat.py`). Use the endpoints there for chat interactions.

## Project Layout (key folders)
- `app/` — application package and entrypoint
- `app/routes/` — API routes (`chat.py`, `cart.py`)
- `app/services/` — core business logic and services
- `app/llm/` — LLM provider interfaces and templates
- `alembic/` — DB migrations

## Development notes
- Models live in `app/models` and are wired by SQLAlchemy in `app/database`.
- To switch LLM provider, set `LLM_PROVIDER` in your env and configure API keys.


