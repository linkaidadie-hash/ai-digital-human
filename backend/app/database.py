"""
Database configuration and table creation for SQLite.
"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database.db"


def get_db_connection():
    """Get database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database and create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Assets table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    # Projects table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        )
    """)

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
    """Get a setting value from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    """Set a setting value in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()