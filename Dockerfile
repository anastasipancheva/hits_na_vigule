FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

COPY . .
COPY .env .env

EXPOSE 8000

CMD ["uvicorn", "controller.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-use-colors"]