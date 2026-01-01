FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY server/ ./server/
COPY pre-processing/ ./pre-processing/

# Set working directory
WORKDIR /app/server

# Expose port
EXPOSE 5000

# Run Flask
CMD ["python", "app.py"]
