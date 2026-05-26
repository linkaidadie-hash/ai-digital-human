"""
Database configuration and table creation for SQLite.
"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Assets table (V1.2: + fps, codec, has_audio, file_size)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            path TEXT NOT NULL,
            tags TEXT DEFAULT '',
            duration REAL DEFAULT 0.0,
            width INTEGER DEFAULT 0,
            height INTEGER DEFAULT 0,
            fps REAL DEFAULT 0.0,
            codec TEXT DEFAULT '',
            has_audio INTEGER DEFAULT 0,
            file_size INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add new columns if they don't exist (migration for existing DB)
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN fps REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN codec TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN has_audio INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN file_size INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # Templates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            main_video_asset_id INTEGER,
            background_asset_id INTEGER,
            product_asset_id INTEGER,
            bgm_asset_id INTEGER,
            subtitle_style_json TEXT DEFAULT '{}',
            layout_json TEXT DEFAULT '{}',
            output_width INTEGER DEFAULT 1080,
            output_height INTEGER DEFAULT 1920,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (main_video_asset_id) REFERENCES assets(id),
            FOREIGN KEY (background_asset_id) REFERENCES assets(id),
            FOREIGN KEY (product_asset_id) REFERENCES assets(id),
            FOREIGN KEY (bgm_asset_id) REFERENCES assets(id)
        )
    """)

    # Projects table (V1.2: + bgm_asset_id, product_asset_id, subtitle_style)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            template_id INTEGER,
            script_text TEXT DEFAULT '',
            voice TEXT DEFAULT '',
            audio_path TEXT DEFAULT '',
            subtitle_path TEXT DEFAULT '',
            output_path TEXT DEFAULT '',
            status TEXT DEFAULT 'draft',
            progress INTEGER DEFAULT 0,
            error TEXT DEFAULT '',
            main_video_asset_id INTEGER,
            background_asset_id INTEGER,
            product_asset_id INTEGER,
            bgm_asset_id INTEGER,
            subtitle_style_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)

    # Migrate existing projects table
    for col, coltype in [
        ("main_video_asset_id", "INTEGER"),
        ("background_asset_id", "INTEGER"),
        ("product_asset_id", "INTEGER"),
        ("bgm_asset_id", "INTEGER"),
        ("subtitle_style_json", "TEXT DEFAULT '{}'"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError:
            pass

    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at: {DATABASE_PATH}")


def get_setting(key: str, default: str = None) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()