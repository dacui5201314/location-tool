"""SQLite 数据库配置 (SQLAlchemy) — WAL 模式提升并发写入"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

import os
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "location_tool.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

# ★ 启用 WAL (Write-Ahead Logging) 模式 — 读写并发不互斥
# ★ 设置 busy_timeout 减少并发写入时 database is locked
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """创建所有表 + 兼容迁移"""
    from models.db_models import User, AnalysisRecord, SavedLocation, RedeemCode, SystemConfig, BillingRecord, OperationLog, BusinessIndustry, PaymentOrder, Feedback  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # ── 轻量兼容迁移：给已有 users 表补 nickname 列 ──
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'nickname' not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN nickname VARCHAR(80) DEFAULT ''")
            conn.commit()
            print("[DB] 已为 users 表添加 nickname 列", flush=True)
        # ── 3288c19: 为 analysis_records 添加 share_token 列 ──
        cols = [r[1] for r in conn.execute("PRAGMA table_info(analysis_records)").fetchall()]
        if 'share_token' not in cols:
            conn.execute("ALTER TABLE analysis_records ADD COLUMN share_token VARCHAR(64) DEFAULT NULL")
            conn.commit()
            print("[DB] 已为 analysis_records 表添加 share_token 列", flush=True)
        # ── 21e8d08: 为 amap_keys 建表 ──
        from models.db_models import AmapKey  # noqa: F401
        Base.metadata.create_all(bind=engine, tables=[AmapKey.__table__])
        # ── b13ab22: 为 saved_locations 添加 latest_report_uuid ──
        cols_sl = [r[1] for r in conn.execute("PRAGMA table_info(saved_locations)").fetchall()]
        if 'latest_report_uuid' not in cols_sl:
            conn.execute("ALTER TABLE saved_locations ADD COLUMN latest_report_uuid VARCHAR(32) DEFAULT ''")
            conn.commit()
            print("[DB] 已为 saved_locations 表添加 latest_report_uuid 列", flush=True)
        # ── 虚拟支付: 为 payment_orders 添加 pay_channel ──
        cols_po = [r[1] for r in conn.execute("PRAGMA table_info(payment_orders)").fetchall()]
        if 'pay_channel' not in cols_po:
            conn.execute("ALTER TABLE payment_orders ADD COLUMN pay_channel VARCHAR(20) DEFAULT 'WECHAT_JSAPI'")
            conn.commit()
            print("[DB] 已为 payment_orders 表添加 pay_channel 列", flush=True)
        # ── 虚拟支付: 为 users 添加 wx_session_key ──
        cols_users = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'wx_session_key' not in cols_users:
            try:
                conn.execute("ALTER TABLE users ADD COLUMN wx_session_key TEXT")
                conn.commit()
                print("[DB] 已为 users 表添加 wx_session_key 列", flush=True)
            except Exception as e:
                print(f"[DB] 添加 users.wx_session_key 失败: {e}", flush=True)
        # ── 反馈: 为 feedbacks 添加截图、报告上下文与回复字段 ──
        try:
            cols_fb = [r[1] for r in conn.execute("PRAGMA table_info(feedbacks)").fetchall()]
            fb_migrations = [
                ("image_urls", "TEXT DEFAULT '[]'"),
                ("credits_granted", "INTEGER DEFAULT 0"),
                ("report_uuid", "VARCHAR(64) DEFAULT ''"),
                ("report_title", "VARCHAR(200) DEFAULT ''"),
                ("report_address", "TEXT DEFAULT ''"),
                ("source", "VARCHAR(40) DEFAULT 'profile'"),
                ("status", "VARCHAR(20) DEFAULT 'pending'"),
                ("admin_reply", "TEXT DEFAULT ''"),
                ("replied_at", "DATETIME DEFAULT NULL"),
                ("updated_at", "DATETIME DEFAULT NULL"),
            ]
            for col_name, col_def in fb_migrations:
                if col_name not in cols_fb:
                    conn.execute(f"ALTER TABLE feedbacks ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    print(f"[DB] 已为 feedbacks 表添加 {col_name} 列", flush=True)
        except Exception:
            pass
        # ── 兼容迁移: 为 analysis_records 补齐所有字段 ──
        cols_ar = [r[1] for r in conn.execute("PRAGMA table_info(analysis_records)").fetchall()]
        ar_migrations = [
            ("report_uuid", "VARCHAR(32) DEFAULT ''"),
            ("report_file", "VARCHAR(500) DEFAULT ''"),
            ("report_url", "VARCHAR(500) DEFAULT ''"),
            ("is_pdf_unlocked", "INTEGER DEFAULT 0"),
            ("share_token", "VARCHAR(64) DEFAULT NULL"),
        ]
        for col_name, col_def in ar_migrations:
            if col_name not in cols_ar:
                try:
                    conn.execute(f"ALTER TABLE analysis_records ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    print(f"[DB] 已为 analysis_records 表添加 {col_name} 列", flush=True)
                except Exception as e:
                    print(f"[DB] 添加 analysis_records.{col_name} 失败: {e}", flush=True)
        conn.close()
    except Exception as e:
        print(f"[DB] 迁移检查跳过: {e}", flush=True)


def get_db():
    """每个请求获取独立的数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
