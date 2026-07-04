FROM python:3.11-slim

WORKDIR /workspace

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY . .

# Create necessary directories in the docker environment
RUN mkdir -p indexes data

# Expose default port (Railway overrides this with $PORT at runtime)
EXPOSE 8000

# Healthcheck — generous start-period so SentenceTransformer model has time to load
# Uses $PORT so it works both locally (8000) and on Railway (dynamic port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/health')" || exit 1

# Shell-form CMD so Railway's $PORT variable is expanded at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
