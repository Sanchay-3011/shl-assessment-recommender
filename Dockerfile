FROM python:3.11-slim

WORKDIR /workspace

# Install build dependencies if needed (e.g., compile-time requirements for rank-bm25 or faiss, though pre-built wheels usually exist)
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

# Expose FastAPI port
EXPOSE 8000

# Add healthcheck to verify container status
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Set default command to run Uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
