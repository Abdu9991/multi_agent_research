FROM python:3.13-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "" appuser

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 10000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} app:app"]