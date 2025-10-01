# Aurora Pro AI - API Documentation

## Overview

Aurora Pro AI is a production-grade AI Operating System with multi-agent orchestration, browser automation, local LLM inference, and comprehensive self-healing capabilities.

## Architecture

- **FastAPI Backend**: RESTful API with async support
- **Streamlit GUI**: Interactive web interface
- **Redis Cache**: Fast in-memory caching
- **SQLite Database**: Persistent data storage
- **Ollama Integration**: Local LLM inference
- **Multi-Agent System**: Orchestrated AI agents

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API uses JWT token-based authentication (can be configured in production).

## Health Endpoints

### GET /health/
Basic health check

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00",
  "service": "aurora-pro-ai"
}
```

### GET /health/live
Kubernetes liveness probe

**Response:**
```json
{
  "status": "alive"
}
```

### GET /health/ready
Kubernetes readiness probe with dependency checks

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": true,
    "cache": true
  },
  "timestamp": "2025-01-01T00:00:00"
}
```

## Agent Endpoints

### GET /api/v1/agents/
List all registered agents

**Response:**
```json
[
  {
    "name": "agent-1",
    "description": "LLM Agent",
    "status": "idle",
    "config": {},
    "created_at": "2025-01-01T00:00:00",
    "last_run": null
  }
]
```

### POST /api/v1/agents/
Create a new agent

**Request Body:**
```json
{
  "name": "my-agent",
  "agent_type": "llm",
  "model_name": "llama2",
  "provider": "ollama",
  "description": "My custom agent",
  "config": {}
}
```

**Response:**
```json
{
  "name": "my-agent",
  "description": "My custom agent",
  "status": "idle",
  "config": {},
  "created_at": "2025-01-01T00:00:00"
}
```

### GET /api/v1/agents/{agent_name}
Get agent information

**Response:**
```json
{
  "name": "my-agent",
  "description": "My custom agent",
  "status": "idle",
  "config": {},
  "created_at": "2025-01-01T00:00:00"
}
```

### DELETE /api/v1/agents/{agent_name}
Delete an agent

**Response:**
```json
{
  "message": "Agent my-agent deleted successfully"
}
```

## Model Endpoints

### GET /api/v1/models/
List all loaded models

**Response:**
```json
{
  "models": {
    "model:ollama:llama2": {
      "name": "llama2",
      "provider": "ollama",
      "loaded_at": "2025-01-01T00:00:00"
    }
  },
  "count": 1
}
```

### POST /api/v1/models/load
Load a model

**Request Body:**
```json
{
  "name": "llama2",
  "provider": "ollama",
  "config": {}
}
```

**Response:**
```json
{
  "message": "Model llama2 loaded successfully",
  "name": "llama2",
  "provider": "ollama"
}
```

### DELETE /api/v1/models/{model_name}
Unload a model

**Query Parameters:**
- `provider` (optional): Model provider (default: "ollama")

**Response:**
```json
{
  "message": "Model llama2 unloaded successfully"
}
```

## Task Endpoints

### POST /api/v1/tasks/execute
Execute a single task

**Request Body:**
```json
{
  "agent": "my-agent",
  "prompt": "Hello, what can you do?",
  "parameters": {}
}
```

**Response:**
```json
{
  "result": "Processed by llama2: Hello, what can you do?...",
  "status": "completed",
  "model": "llama2",
  "provider": "ollama",
  "tokens_used": 5,
  "completed_at": "2025-01-01T00:00:00"
}
```

### POST /api/v1/tasks/execute/batch
Execute multiple tasks

**Request Body:**
```json
{
  "tasks": [
    {
      "agent": "my-agent",
      "prompt": "Task 1",
      "parameters": {}
    },
    {
      "agent": "my-agent",
      "prompt": "Task 2",
      "parameters": {}
    }
  ]
}
```

**Response:**
```json
[
  {
    "result": "...",
    "status": "completed",
    "completed_at": "2025-01-01T00:00:00"
  },
  {
    "result": "...",
    "status": "completed",
    "completed_at": "2025-01-01T00:00:00"
  }
]
```

## Metrics Endpoint

### GET /metrics
Prometheus metrics endpoint (when enabled)

Returns metrics in Prometheus format.

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Rate limiting is configurable via environment variables:
- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting
- `RATE_LIMIT_PER_MINUTE`: Requests per minute per IP

## Interactive API Documentation

Visit `/docs` for interactive Swagger UI documentation.
Visit `/redoc` for ReDoc documentation.
