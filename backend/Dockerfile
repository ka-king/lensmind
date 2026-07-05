FROM python:3.11-slim

WORKDIR /app

# System dependencies for FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[dev]

# Source
COPY packages/ packages/

# Run gateway
CMD ["uvicorn", "app.gateway.app:app", "--host", "0.0.0.0", "--port", "8001"]
