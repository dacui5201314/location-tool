"""轻量迁移 runner：按版本号顺序执行 SQL，幂等。"""
import os, sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent
SCHEMA_TABLE = "schema_migrations"


def _ensure_schema_table(conn):
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {SCHEMA_TABLE} (
        version TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""")
    conn.commit()


def run_migrations(db_path: str):
    """执行所有未应用的迁移（幂等）。"""
    conn = sqlite3.connect(db_path)
    _ensure_schema_table(conn)

    applied = {r[0] for r in conn.execute(f"SELECT version FROM {SCHEMA_TABLE}").fetchall()}
    sql_files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))

    for fname in sql_files:
        version = fname.replace(".sql", "")
        if version in applied:
            continue
        sql_path = MIGRATIONS_DIR / fname
        sql = sql_path.read_text(encoding="utf-8")
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    continue
                raise
        conn.execute(f"INSERT INTO {SCHEMA_TABLE} (version) VALUES (?)", (version,))
        conn.commit()
        print(f"[Migration] applied {version}", flush=True)
    conn.close()
