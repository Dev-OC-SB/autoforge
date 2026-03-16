FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Install UI dependencies and build
RUN cd ui && npm install && npm run build

# Expose ports
# 8888: Main server
# 5173: UI (if running in dev mode)
EXPOSE 8888 5173

# Environment variables (can be overridden via docker-compose or -e flags)
ENV AUTOFORGE_PROVIDER=auto
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Run the UI server by default
CMD ["python", "start_ui.py", "--host", "0.0.0.0", "--port", "8888"]
