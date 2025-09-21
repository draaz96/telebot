FROM python:3.11.5-slim-bullseye

# Install system dependencies with retry mechanism
RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    libmagic1 \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create temp directory for file storage
RUN mkdir -p temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app
USER appuser

# Command to run both bot and server
CMD ["python", "src/server.py"]