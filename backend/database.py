"""SQLite 数据库配置 (SQLAlchemy) — WAL 模式提升并发写入"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "location_tool.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

# ★ 启用 WAL (Write-Ahead Logging) 模式 — 读写并发不互斥
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """创建所有表"""
    from models.db_models import User, AnalysisRecord, SavedLocation, RedeemCode, SystemConfig, BillingRecord, OperationLog, BusinessIndustry, PaymentOrder  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """每个请求获取独立的数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
