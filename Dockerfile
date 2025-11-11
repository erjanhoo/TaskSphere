FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libpq-dev \
       gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt

# Copy project
COPY . /app/

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser || true
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command (use django management commands in compose override if needed)
CMD ["gunicorn", "TaskSphere.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
