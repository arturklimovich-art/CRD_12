FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# === УСТАНОВКА СИСТЕМНЫХ ЗАВИСИМОСТЕЙ ===
# Устанавливаем C-библиотеки, необходимые для 'asyncpg' и 'psycopg2-binary'
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt первым (для кэширования слоев)
COPY requirements.txt .

# Устанавливаем все зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы
COPY . .

# ВАША СТАНДАРТНАЯ КОМАНДА
CMD ["python", "bot.py"]
