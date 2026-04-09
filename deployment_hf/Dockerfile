# Use Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies for build and networking
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Requirements and Install
COPY Cybronites/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Project Files
COPY Cybronites/ /app/Cybronites/
COPY blockchain/ /app/blockchain/
COPY dashboard/dist/ /app/static/
COPY run_local.py .

# Environment Variables
ENV PYTHONPATH=/app
ENV PORT=7860
ENV FLOWER_PORT=8080
ENV ROUNDS=5

# Copy Startup Script
COPY deployment_hf/start_cloud.sh .
RUN chmod +x start_cloud.sh

# Expose Bridge Port
EXPOSE 7860

# CMD to start the orchestrator
CMD ["./start_cloud.sh"]
