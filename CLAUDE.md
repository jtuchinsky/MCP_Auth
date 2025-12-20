# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based web application project called "mcp-auth". The project is currently in early development (v0.1.0) with a minimal API structure.

## Technology Stack

- **Framework**: FastAPI (>=0.126.0)
- **ASGI Server**: Uvicorn (>=0.38.0)
- **Python Version**: >=3.12
- **Dependency Management**: uv (based on uv.lock presence)

## Project Structure

```
MCP_Auth/
├── main.py              # Main FastAPI application with route definitions
├── pyproject.toml       # Project metadata and dependencies
├── test_main.http       # HTTP test requests (JetBrains HTTP Client format)
└── .venv/              # Virtual environment
```

## Development Commands

### Running the Application

```bash
# Development server with auto-reload
uvicorn main:app --reload

# Production server
uvicorn main:app
```

The server runs on `http://127.0.0.1:8000` by default.

### Dependency Management

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package-name>
```

### Testing

The project includes `test_main.http` for manual API testing using JetBrains HTTP Client (available in PyCharm/IntelliJ IDEA).

## API Structure

The application (`main.py`) currently defines:
- Root endpoint: `GET /` - Returns a hello world message
- Parameterized endpoint: `GET /hello/{name}` - Returns a personalized greeting

All endpoints are async functions following FastAPI conventions.

## Code Conventions

- Use async/await for route handlers
- FastAPI app instance is named `app` in main.py
- Endpoint functions follow the pattern: `async def function_name(...)`