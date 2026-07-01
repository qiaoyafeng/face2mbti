# Use Python 3.13 slim image
FROM python:3.13-slim

# Use Alibaba Cloud mirrors for apt and pip
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# Install curl for healthcheck, ffmpeg for video processing, and uv
RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Configure uv to use Alibaba Cloud PyPI mirror
ENV UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies (creates .venv)
RUN uv sync --frozen --no-dev --link-mode=copy

# Copy application code
COPY app/ ./app/

# Expose port (default 8000, override via APP_PORT env)
ENV APP_PORT=8000
EXPOSE ${APP_PORT}

# Run the application
CMD uv run uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}
