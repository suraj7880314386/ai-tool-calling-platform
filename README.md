# AI Agent Tool-Calling API Platform

A production-ready LLM-powered agent system with tool-calling capabilities (web search, calculator, database query, weather, Wikipedia) built with LangChain, FastAPI, and Docker.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     FastAPI Backend                       │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────┐ │
│  │ /execute  │  │ /tools   │  │ /history  │  │/health │ │
│  └─────┬─────┘  └──────────┘  └───────────┘  └────────┘ │
│        │                                                  │
│  ┌─────▼──────────────────────────────────────────────┐  │
│  │              LangChain Agent Executor               │  │
│  │   ┌─────────────────────────────────────────────┐  │  │
│  │   │         Tool Router + Retry Logic            │  │  │
│  │   └──┬──────┬──────┬──────┬──────┬──────────────┘  │  │
│  │      │      │      │      │      │                  │  │
│  │   ┌──▼─┐ ┌─▼──┐ ┌─▼──┐ ┌▼───┐ ┌▼─────┐           │  │
│  │   │Web │ │Calc│ │ DB │ │Wiki│ │Weathr│           │  │
│  │   │Srch│ │    │ │Qry │ │    │ │      │           │  │
│  │   └────┘ └────┘ └──┬─┘ └────┘ └──────┘           │  │
│  └─────────────────────┼─────────────────────────────┘  │
│                        │                                  │
│  ┌─────────────────────▼──────────────────────────────┐  │
│  │              PostgreSQL Database                     │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Structured Output Parser                │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Features

- **5 Built-in Tools**: Web Search, Calculator, Database Query, Wikipedia, Weather
- **LangChain Agent**: ReAct agent with automatic tool selection and chaining
- **Structured Outputs**: Pydantic-validated JSON responses from LLM
- **Retry Logic**: Exponential backoff with configurable max retries
- **Rate Limiting**: Per-endpoint rate limiting with SlowAPI
- **Streaming**: SSE streaming for real-time agent thought process
- **Execution History**: Full audit trail of agent decisions and tool calls
- **Docker Deployment**: Docker Compose with PostgreSQL

## Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Agent**: LangChain (ReAct Agent)
- **LLM**: OpenAI GPT-4 (configurable)
- **Database**: PostgreSQL + SQLAlchemy
- **Rate Limiting**: SlowAPI
- **Containerization**: Docker + Docker Compose

## Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/yourusername/ai-tool-calling-platform.git
cd ai-tool-calling-platform
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### 2. Run with Docker
```bash
docker-compose up --build
```

### 3. Run Locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Try it
```bash
# Simple query — agent auto-selects the right tool
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 25 * 48 + 132?"}'

# Web search
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "Latest news about SpaceX Starship launch"}'

# Database query
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "Show all users who signed up in the last 7 days"}'

# Multi-tool chain
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the population of Tokyo and what is that divided by 1000?"}'
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/execute` | Execute agent with auto tool selection |
| POST | `/api/v1/execute/stream` | Stream agent execution (SSE) |
| GET | `/api/v1/tools` | List all available tools |
| GET | `/api/v1/tools/{name}` | Get tool details |
| GET | `/api/v1/history` | Get execution history |
| GET | `/api/v1/history/{exec_id}` | Get specific execution details |
| GET | `/api/v1/health` | Health check |

## Project Structure

```
ai-tool-calling-platform/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration
│   ├── api/
│   │   ├── routes.py        # API endpoints
│   │   └── schemas.py       # Pydantic models
│   ├── agents/
│   │   ├── executor.py      # LangChain agent executor
│   │   └── retry.py         # Retry logic with backoff
│   ├── tools/
│   │   ├── registry.py      # Tool registry & manager
│   │   ├── search.py        # Web search tool
│   │   ├── calculator.py    # Math calculator tool
│   │   ├── database.py      # SQL database query tool
│   │   ├── wikipedia.py     # Wikipedia lookup tool
│   │   └── weather.py       # Weather lookup tool
│   └── core/
│       ├── database.py       # SQLAlchemy setup
│       ├── models.py         # DB models
│       └── history.py        # Execution history manager
├── tests/
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT
