FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Default matches Ollama nomic-embed-text; override at runtime if you use another model/width
ENV EMBEDDING_DIMENSIONS=768

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY sql ./sql

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
