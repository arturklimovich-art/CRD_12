FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остального кода (будет переопределено bind mount в docker-compose)
COPY . .

# Создание workspace директорий
RUN mkdir -p /app/workspace/patches \
    /app/workspace/reports \
    /app/workspace/snapshots \
    /app/workspace/ADR \
    /app/workspace/logs \
    /app/workspace/patches_applied \
    /app/agents

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 8030

# Команда запуска
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
