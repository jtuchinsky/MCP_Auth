# Unit Tests

This directory contains unit tests for individual components of the MCP Auth Service.

## Test Files

### test_database.py

Tests for database configuration and session management (Step 3).

**Test Coverage:**
- ✅ Base declarative class is properly defined
- ✅ SQLAlchemy engine is created correctly
- ✅ Engine can establish database connection
- ✅ SessionLocal factory is created
- ✅ SessionLocal creates valid sessions
- ✅ SessionLocal has correct configuration (autoflush disabled)
- ✅ `get_db()` dependency yields valid sessions
- ✅ `get_db()` properly closes sessions after use
- ✅ `get_db()` works as a context manager
- ✅ `get_db()` handles exceptions gracefully
- ✅ Base.metadata is accessible for migrations
- ✅ Database can be inspected using SQLAlchemy inspector

**Running Tests:**
```bash
# Run all database tests
uv run pytest tests/unit/test_database.py -v

# Run specific test class
uv run pytest tests/unit/test_database.py::TestDatabaseConfiguration -v

# Run specific test
uv run pytest tests/unit/test_database.py::TestDatabaseConfiguration::test_engine_connects -v
```

**Test Results:**
```
12 passed in 0.23s
```

## Running All Unit Tests

```bash
uv run pytest tests/unit/ -v
```

## Test Coverage

To run tests with coverage:
```bash
uv run pytest tests/unit/ --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```
