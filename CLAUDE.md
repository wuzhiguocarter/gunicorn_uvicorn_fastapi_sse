# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a high-performance ChatBot server built with FastAPI, supporting Server-Sent Events (SSE) for real-time streaming responses. The server supports multi-turn conversations and is optimized for production deployment with gunicorn and uvicorn. The project includes comprehensive load testing capabilities with progressive ramp-up testing and detailed performance reporting.

## Key Commands

### Environment Setup
```bash
# Create virtual environment and install dependencies
uv venv --python 3.12
uv pip install -e ".[dev]"

# Setup development environment
make setup-dev
```

### Running the Server
```bash
# Development mode with auto-reload
make run-dev

# Production mode with gunicorn
make run-gunicorn

# Demo mode with web interface
make demo
```

### Testing
```bash
# Run all tests
make test

# Run tests with coverage
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
make pre-commit  # pre-commit hooks
```

### Load Testing
```bash
# Simple load test
make load-test

# Full load test
make load-test-full

# Ramp-up load test
make load-test-ramp

# Progressive ramp-up test with visual progress
uv run python ramp_up_test.py
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

### Progressive Ramp-up Testing (`ramp_up_test.py`)
- **Visual Progress Tracking**: Real-time progress bars with system resource monitoring
- **9 Test Phases**: From 10 to 200 concurrent users with automatic escalation
- **Comprehensive Reporting**: JSON results and Markdown reports with performance analysis
- **System Monitoring**: Real-time CPU and memory usage tracking during tests
- **Interactive UI**: Health check progress, phase transitions, and countdown timers

### Test Scenarios
- **Concurrent Testing**: Fixed number of concurrent requests
- **Ramp-up Testing**: Gradual increase in concurrent users
- **Multi-turn Testing**: Maintains conversation context across requests
- **Progressive Load Testing**: Step-by-step concurrency increase with performance analysis

### Report Generation
- **Timestamped Directories**: All test results saved to `reports/YYmmddTHHMM/` format
- **Dual Output**: Both JSON data files and Markdown human-readable reports
- **Performance Analysis**: Automatic detection of performance bottlenecks and trends
- **System Metrics**: CPU, memory, and response time analysis across all test phases

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

### Load Testing Development
- **New Test Scenarios**: Add new test patterns to `src/load_test/client.py`
- **Progressive Testing**: Extend `ramp_up_test.py` with additional test phases or metrics
- **Report Generation**: Enhance reporting functionality in the progressive testing framework
- **Performance Analysis**: Add new performance metrics or analysis methods

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
├── reports/                     # Load test reports and results
├── gunicorn.conf.py             # Gunicorn configuration
├── start.sh                     # Production startup script
├── ramp_up_test.py              # Progressive load testing with UI
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
- `SSE_KEEPALIVE_TIMEOUT`: SSE keepalive timeout in seconds (default: 30)
- `SSE_RECONNECT_DELAY`: SSE reconnect delay in milliseconds (default: 1000)
- `MAX_CONCURRENT_CONNECTIONS`: Maximum concurrent connections (default: 1000)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `API_KEY`: Optional API key for authentication
- `CORS_ORIGINS`: CORS allowed origins (default: ["*"])
