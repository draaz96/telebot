FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
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

# Command to run both bot and server
CMD ["python", "src/server.py"]