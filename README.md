# ChatBot SSE Server

A high-performance ChatBot server built with FastAPI, supporting Server-Sent Events (SSE) for real-time streaming responses. This server supports multi-turn conversations and is optimized for production deployment with gunicorn and uvicorn.

## Features

- **Server-Sent Events (SSE)**: Real-time streaming responses
- **Multi-turn Conversations**: Maintains conversation context
- **High Performance**: Deployed with gunicorn + uvicorn workers
- **Load Testing**: Built-in load testing tools
- **Comprehensive Testing**: Full test suite with pytest
- **Code Quality**: Integrated linting and type checking
- **Metrics & Monitoring**: Health checks and performance metrics

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd gunicorn_uvicorn_fastapi_sse

# Install dependencies
make install
```

### Development Setup

```bash
# Install development dependencies
make dev-install

# Set up pre-commit hooks
make setup-dev
```

### Running the Server

**Development Mode:**
```bash
make run-dev
```

**Production Mode:**
```bash
make run-gunicorn
```

**Simple Demo:**
```bash
make demo
```

### Testing

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run all quality checks
make check-all
```

### Load Testing

```bash
# Simple load test
make load-test

# Full load test with 100 requests, 10 concurrent
make load-test-full

# Ramp-up load test
make load-test-ramp
```

## API Documentation

### Endpoints

#### `GET /`
Web interface for testing the ChatBot

#### `POST /chat`
Send a message and receive streaming response via SSE

**Parameters:**
- `message` (required): The message to send
- `conversation_id` (optional): ID of existing conversation

**Response:** Server-Sent Events stream with events:
- `connected`: Connection established
- `message`: Partial response chunk
- `completed`: Full response complete
- `error`: Error occurred

#### `GET /health`
Health check endpoint

#### `GET /metrics`
Performance metrics endpoint

#### `GET /conversations/{conversation_id}/history`
Get conversation history

### Example Usage

```python
import requests
import json

# Start a conversation
response = requests.post(
    "http://localhost:8000/chat",
    data={"message": "Hello, how are you?"}
)

# Process SSE stream
for line in response.iter_lines():
    if line.startswith(b'data: '):
        data = json.loads(line[6:])
        print(f"Event: {data.get('type')}")
        print(f"Content: {data.get('content', '')}")
```

## Configuration

### Environment Variables

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: False)
- `MAX_HISTORY_LENGTH`: Maximum conversation history length (default: 10)
- `RESPONSE_DELAY`: Simulated response delay in seconds (default: 0.5)
- `LOG_LEVEL`: Logging level (default: INFO)
- `WORKERS`: Number of gunicorn workers (default: CPU cores * 2 + 1)

### Gunicorn Configuration

The server includes optimized gunicorn configuration for production deployment:

- **Worker Class**: `uvicorn.workers.UvicornWorker`
- **Worker Processes**: `CPU cores * 2 + 1`
- **Worker Connections**: 1000
- **Timeout**: 30 seconds
- **Keepalive**: 2 seconds

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
├── logs/
├── pyproject.toml
├── gunicorn.conf.py
├── requirements.txt
├── start.sh
├── Makefile
└── README.md
```

## Development

### Code Quality

The project uses multiple tools to ensure code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **ruff**: Fast linting
- **mypy**: Type checking
- **pytest**: Testing framework

### Running Tests

```bash
# Run specific test file
python -m pytest src/tests/test_models.py -v

# Run with coverage
python -m pytest src/tests/ --cov=src/app --cov-report=html

# Run specific test
python -m pytest src/tests/test_models.py::TestMessage::test_message_creation -v
```

### Type Checking

```bash
# Run type checking
make type-check

# Run type checking with strict mode
mypy --strict src/app/
```

## Performance Optimization

### Gunicorn Tuning

- **Worker Count**: Adjust based on CPU cores and workload
- **Worker Connections**: Set based on expected concurrent users
- **Timeout**: Adjust based on response time requirements
- **Keepalive**: Optimize for connection reuse

### Load Testing

The project includes comprehensive load testing tools:

```bash
# Concurrent test
python src/load_test/scripts/run_load_test.py \
    --requests 1000 \
    --concurrency 50 \
    --multi-turn

# Ramp-up test
python src/load_test/scripts/run_load_test.py \
    --ramp-up 60 \
    --duration 300 \
    --concurrency 100
```

## Deployment

### Docker Deployment

```bash
# Build Docker image
docker build -t chatbot-sse-server .

# Run container
docker run -p 8000:8000 chatbot-sse-server
```

### Systemd Service

Create a systemd service file:

```ini
[Unit]
Description=ChatBot SSE Server
After=network.target

[Service]
Type=notify
User=chatbot
Group=chatbot
WorkingDirectory=/opt/chatbot-sse-server
Environment=PATH=/opt/chatbot-sse-server/venv/bin
ExecStart=/opt/chatbot-sse-server/venv/bin/gunicorn -c gunicorn.conf.py src.app.main:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

## Monitoring

### Health Checks

The server provides comprehensive health checks:

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

### Logging

Structured logging is configured with `structlog`:

```python
from src.app.logger import get_logger

logger = get_logger(__name__)
logger.info("event_occurred", key="value")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

### Development Workflow

```bash
# 1. Install development dependencies
make setup-dev

# 2. Make changes
# 3. Run quality checks
make check-all

# 4. Run tests
make test

# 5. Commit changes
git add .
git commit -m "feat: add new feature"

# 6. Push changes
git push origin feature-branch
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.