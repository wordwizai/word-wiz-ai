# -------------------------
# Stage 1: Build stage
# -------------------------
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to leverage Docker cache
COPY requirements.txt .

# Install CPU-only PyTorch
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install dependencies in a separate folder to copy later
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------
# Stage 2: Final stage
# -------------------------
FROM python:3.12-slim

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /usr/local /usr/local

# Copy project files (excluding large or sensitive files via .dockerignore)
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the app with Gunicorn and Uvicorn workers
CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
