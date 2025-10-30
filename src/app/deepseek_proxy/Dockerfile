# src/app/deepseek_proxy/Dockerfile

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED 1

# --- КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Установка wget для healthcheck ---
RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/*
# -------------------------------------------------------------

# Сначала копируем только файл требований для лучшего кеширования слоев Docker
COPY requirements.txt .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем само приложение
COPY app.py .

# Запуск приложения на порту 8010
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]