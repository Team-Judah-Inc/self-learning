# Use an official Python slim image for a smaller footprint
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Set environment variables
# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py

# Install system dependencies if needed (e.g., for certain crypto libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the data directory if it doesn't exist
RUN mkdir -p mock_data

# Expose the port Flask runs on
EXPOSE 5000

# Make the start script executable
RUN chmod +x start.sh

# Command to run the application
CMD ["./start.sh"]