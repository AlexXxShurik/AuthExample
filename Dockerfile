FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl gcc libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi --without dev

COPY alembic.ini ./
COPY backend ./backend
COPY db ./db

RUN mkdir -p /app/backend/app/uploads

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
