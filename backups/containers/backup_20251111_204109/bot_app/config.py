# src/bot/config.py
from __future__ import annotations
import os

# =========================
# API keys / endpoints
# =========================
# Берём из окружения; по умолчанию — пустые строки (без небезопасных заглушек)
DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Прокси DeepSeek (совместимо с вашим deepseek_proxy)
DEEPSEEK_PROXY_URL: str = os.getenv("DEEPSEEK_PROXY_URL", "http://deepseek_proxy:8010/llm/complete").rstrip("/")

# Внутрисетевой адрес Engineer B API (имя сервиса из docker-compose)
ENGINEER_B_API_URL: str = os.getenv("ENGINEER_B_API_URL", "http://engineer_b_api:8000").rstrip("/")

# =========================
# Database DSN
# =========================
# Правило: читаем из окружения; если не задано — локальный SQLite (для простого запуска без Docker)
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///tasks.db")


def _normalize_dsn(dsn: str) -> str:
    """
    Нормализует DSN, чтобы SQLAlchemy и драйверы открывались без сюрпризов.
    - postgres:// → postgresql+psycopg2://
    - sqlite+aiosqlite:/// → sqlite:///
    """
    if dsn.startswith("postgres://"):
        # старый шорткат → явная схема драйвера
        dsn = dsn.replace("postgres://", "postgresql+psycopg2://", 1)
    if dsn.startswith("sqlite+aiosqlite:///"):
        dsn = dsn.replace("sqlite+aiosqlite:///", "sqlite:///", 1)
    return dsn


DATABASE_URL = _normalize_dsn(DATABASE_URL)

# =========================
# Code Interpreter
# =========================
# Таймаут исполнения «песочницы» в секундах
INTERPRETER_TIMEOUT: int = int(os.getenv("INTERPRETER_TIMEOUT", "30"))
