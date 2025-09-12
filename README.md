# ZERO-COMP Solar Weather API

Real-time solar flare prediction API powered by NASA-IBM's Surya-1.0 model.

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application setup
├── config.py            # Configuration management
├── models/              # Pydantic data models
│   ├── __init__.py
│   └── core.py          # Core data structures
├── services/            # Business logic services
│   └── __init__.py
├── repositories/        # Data access layer
│   └── __init__.py
└── api/                 # API endpoints
    └── __init__.py
```

## Setup

1. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the development server:
   ```bash
   python -m app.main
   ```

## API Documentation

When running in debug mode, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Health Check

Check API health at: http://localhost:8000/health