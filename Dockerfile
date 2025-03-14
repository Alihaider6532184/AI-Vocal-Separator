FROM python:3.9-slim

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for uploads and processed files
RUN mkdir -p app/uploads app/processed

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"] 