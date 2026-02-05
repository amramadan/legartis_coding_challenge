FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* /app/
RUN uv sync --no-dev

COPY app /app/app

EXPOSE 8000

CMD ["uv", "run", "flask", "--app", "app.api.app_factory:create_app", "run", "--host", "0.0.0.0", "--port", "8000"]
