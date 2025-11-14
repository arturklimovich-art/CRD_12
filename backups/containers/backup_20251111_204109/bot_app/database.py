# src/bot/database.py
from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import sessionmaker, declarative_base

# Попытка JSONB для Postgres; в остальных СУБД будет Text
try:
    from sqlalchemy.dialects.postgresql import JSONB  # type: ignore
    HAS_JSONB = True
except Exception:
    HAS_JSONB = False

log = logging.getLogger("db")

# ---- 1) Берём DSN из окружения, при отсутствии — из config.py ----
ENV_DSN = os.getenv("DATABASE_URL")
if not ENV_DSN:
    try:
        from config import DATABASE_URL as CFG_DSN  # type: ignore
        ENV_DSN = CFG_DSN
    except Exception:
        ENV_DSN = None

if not ENV_DSN:
    raise RuntimeError(
        "DATABASE_URL is not set. Example: "
        "postgresql+psycopg2://crd_user:crd12@pgvector:5432/crd12 "
        "or sqlite:///tasks.db"
    )

# ---- 2) Жёсткая нормализация DSN здесь (независимо от config.py) ----
DSN = ENV_DSN
if DSN.startswith("postgres://"):
    DSN = DSN.replace("postgres://", "postgresql+psycopg2://", 1)
if DSN.startswith("sqlite+aiosqlite:///"):
    DSN = DSN.replace("sqlite+aiosqlite:///", "sqlite:///", 1)

IS_SQLITE = DSN.startswith("sqlite")
IS_POSTGRES = DSN.startswith("postgresql")

TestResultsType = JSONB if (IS_POSTGRES and HAS_JSONB) else Text

# ---- 3) Engine / Session ----
engine_kwargs = dict(pool_pre_ping=True, future=True)
if IS_SQLITE:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DSN, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()

# ---- 4) Модель ----
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    task_description = Column(Text, nullable=False)

    status = Column(String(32), nullable=False, index=True, default="pending")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    generated_code = Column(Text, nullable=True)
    test_results = Column(TestResultsType, nullable=True)  # JSONB в PG, Text в SQLite
    deployment_ready = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"<Task id={self.id} status={self.status}>"

# ---- 5) Инициализация схемы ----
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    log.info("DB initialized. DSN=%s", DSN)

# Инициализация сразу при импорте
init_db()

# ---- 6) Генератор сессий (если где-то используется) ----
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
