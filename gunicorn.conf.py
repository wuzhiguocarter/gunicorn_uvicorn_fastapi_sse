from container_inspect import get_cgroup_cpu_count

# Worker connections
worker_connections = 1000
timeout = 30
keepalive = 2

# Worker processes
workers = get_cgroup_cpu_count()
worker_class = "uvicorn.workers.UvicornWorker"
# Use platform-appropriate temporary directory
import tempfile
worker_tmp_dir = tempfile.gettempdir()

# Logging
loglevel = "info"
errorlog = "-"
accesslog = "-"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Bind address
bind = ["0.0.0.0:8000"]

# Max requests
max_requests = 1000
max_requests_jitter = 100

# Graceful timeout
graceful_timeout = 30

# Preload app
preload_app = True