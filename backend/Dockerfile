FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* /app/
RUN uv sync --no-dev

COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic -c alembic.ini upgrade head && uv run flask --app app.api.app_factory:create_app run --host 0.0.0.0 --port 8000"]
