# Use official Python runtime
FROM python:3.11-slim

# Install AWS Lambda Web Adapter
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    AWS_LWA_INVOKE_MODE=response_stream

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Copy dependency files (from root)
COPY pyproject.toml uv.lock ./

# Install dependencies into system python
RUN uv pip install --system .

# Copy backend code
COPY backend ./backend

# Create a non-root user (Security Best Practice)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application - Lambda Web Adapter will proxy requests to this
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
