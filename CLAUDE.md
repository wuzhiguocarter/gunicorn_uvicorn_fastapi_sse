# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a high-performance ChatBot server built with FastAPI, supporting Server-Sent Events (SSE) for real-time streaming responses. The server supports multi-turn conversations and is optimized for production deployment with gunicorn and uvicorn.

## Key Commands

### Development Environment Setup
```bash
# Create virtual environment with uv and install dependencies
uv venv --python 3.12
uv pip install -e ".[dev]"

# Alternative using make
make setup-dev
```

### Running the Server
```bash
# Development mode with auto-reload
uv run uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode with gunicorn
uv run ./start.sh

# Or using make commands
make run-dev
make run-gunicorn
```

### Testing
```bash
# Run all tests
uv run pytest src/tests/ -v
make test

# Run tests with coverage
uv run pytest src/tests/ --cov=src/app --cov-report=html --cov-report=term-missing
make test-coverage

# Run specific test file
uv run pytest src/tests/test_models.py -v

# Run specific test method
uv run pytest src/tests/test_models.py::TestMessage::test_message_creation -v
```

### Code Quality
```bash
# Run all quality checks
make check-all

# Individual checks
make lint        # ruff linting
make format      # black + isort formatting
make type-check  # mypy type checking

# Run pre-commit hooks
make pre-commit
```

### Load Testing
```bash
# Simple load test
uv run python src/load_test/scripts/run_load_test.py --simple
make load-test

# Full load test with custom parameters
uv run python src/load_test/scripts/run_load_test.py --requests 100 --concurrency 10 --multi-turn

# Ramp-up load test
uv run python src/load_test/scripts/run_load_test.py --ramp-up 30 --duration 60 --concurrency 20
```

## Architecture Overview

### Core Components

1. **FastAPI Application** (`src/app/main.py`):
   - Main FastAPI app with SSE streaming support
   - CORS middleware configuration
   - Request/response metrics middleware
   - Built-in HTML test interface

2. **ChatBot Engine** (`src/app/chatbot.py`):
   - SSE streaming response generator
   - Simulated AI response generation with configurable delays
   - Multi-turn conversation support
   - Error handling and connection management

3. **Conversation Manager** (`src/app/conversation_manager.py`):
   - In-memory conversation state management
   - Connection tracking for active conversations
   - Automatic conversation cleanup
   - Metrics collection and reporting

4. **Data Models** (`src/app/models.py`):
   - Pydantic models for all API interactions
   - Conversation and message structures
   - SSE event models
   - Health check and metrics responses

### Key Design Patterns

- **SSE Streaming**: Uses `sse-starlette` for real-time streaming responses
- **Async/Await**: Fully async implementation for high performance
- **State Management**: In-memory conversation storage with UUID-based identification
- **Metrics Collection**: Comprehensive metrics tracking for performance monitoring
- **Error Handling**: Graceful error handling with proper logging

### SSE Event Flow

1. Client sends POST request to `/chat` endpoint
2. Server establishes SSE connection with `connected` event
3. Server sends multiple `message` events with partial responses
4. Server sends final `completed` event with full response summary
5. Conversation state is persisted for multi-turn support

### Configuration

The application uses environment variables and `pydantic-settings` for configuration:

- **Server Settings**: HOST, PORT, DEBUG
- **SSE Settings**: SSE_KEEPALIVE_TIMEOUT, SSE_RECONNECT_DELAY
- **ChatBot Settings**: MAX_HISTORY_LENGTH, RESPONSE_DELAY
- **Performance**: MAX_CONCURRENT_CONNECTIONS, REQUEST_TIMEOUT

## Load Testing Architecture

### Load Testing Client (`src/load_test/client.py`)
- Async-based load testing client using aiohttp
- Comprehensive metrics collection (response times, success rates, throughput)
- Support for concurrent and ramp-up testing scenarios
- Multi-turn conversation testing support

### Test Scenarios
- **Concurrent Testing**: Fixed number of concurrent requests
- **Ramp-up Testing**: Gradual increase in concurrent users
- **Multi-turn Testing**: Maintains conversation context across requests

## Testing Strategy

### Unit Tests
- Model validation and serialization
- Conversation management logic
- ChatBot response generation
- Error handling scenarios

### Integration Tests
- SSE streaming functionality
- API endpoint behavior
- Multi-turn conversation flows
- Metrics collection accuracy

### Load Tests
- Performance under concurrent load
- Memory usage monitoring
- Connection pooling efficiency
- Response time distribution

## Development Guidelines

### Adding New Features
1. Update corresponding models in `src/app/models.py`
2. Implement business logic in appropriate module
3. Add tests in `src/tests/`
4. Update load testing scenarios if needed
5. Run all quality checks before committing

### Performance Considerations
- Keep conversation history limited (configurable)
- Use async/await consistently
- Monitor memory usage with many conversations
- Consider connection pooling for database/storage operations
- Test with load tools before deploying changes

### Error Handling
- Use structured logging with `structlog`
- Implement graceful degradation
- Provide meaningful error messages in SSE events
- Monitor error rates through metrics endpoint

## Monitoring and Metrics

### Available Metrics
- Request counts and error rates
- Response time distributions
- Active conversation counts
- Connection pooling statistics
- System uptime and health

### Health Checks
- `/health` endpoint for basic health
- `/metrics` endpoint for detailed metrics
- Built-in monitoring middleware
- Docker health check integration

## Dependencies

The project uses modern Python dependencies:
- **FastAPI**: Web framework with automatic API documentation
- **Uvicorn**: ASGI server with WebSocket support
- **Gunicorn**: WSGI server for production deployment
- **sse-starlette**: Server-Sent Events support
- **Pydantic**: Data validation and serialization
- **Structlog**: Structured logging
- **pytest**: Testing framework with async support
- **ruff/black/isort**: Code quality tools
- **mypy**: Type checking

## Project Structure

```
gunicorn_uvicorn_fastapi_sse/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Data models
│   │   ├── chatbot.py           # ChatBot implementation
│   │   ├── conversation_manager.py # Conversation state management
│   │   ├── config.py            # Configuration
│   │   └── logger.py            # Logging setup
│   ├── load_test/
│   │   ├── __init__.py
│   │   ├── client.py            # Load testing client
│   │   ├── simple_client.py     # Simple test client
│   │   └── scripts/
│   │       └── run_load_test.py # Load test script
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py
│       ├── test_main.py
│       ├── test_chatbot.py
│       ├── test_conversation_manager.py
│       └── test_load_test.py
├── gunicorn.conf.py             # Gunicorn configuration
├── start.sh                     # Production startup script
├── Makefile                     # Common commands
├── pyproject.toml               # Project configuration
└── .pre-commit-config.yaml      # Pre-commit hooks
```

## Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: False)
- `MAX_HISTORY_LENGTH`: Maximum conversation history length (default: 10)
- `RESPONSE_DELAY`: Simulated response delay in seconds (default: 0.5)
- `LOG_LEVEL`: Logging level (default: INFO)
- `WORKERS`: Number of gunicorn workers (default: CPU cores * 2 + 1)