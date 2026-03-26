FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies for native Python extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a system user 'appuser'
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser

# Ensure the PATH includes the local bin for the new user
ENV PATH="/home/appuser/.local/bin:${PATH}"

COPY --chown=appuser:appuser . .
RUN pip install --user --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-10000} --workers ${WEB_CONCURRENCY:-1} --timeout ${GUNICORN_TIMEOUT:-180} app:app"]