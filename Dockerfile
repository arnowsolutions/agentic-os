# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8090 \
    HOST=0.0.0.0

WORKDIR /app

# Install system deps needed by some Python packages (numpy, sklearn, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user for runtime security
RUN groupadd -r app && useradd -r -g app app \
    && chown -R app:app /app
USER app

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8090/vapi/status', timeout=4)" || exit 1

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8090"]
