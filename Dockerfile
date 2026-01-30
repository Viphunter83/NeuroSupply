FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy project code
COPY . .

# Default command (can be overridden)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
