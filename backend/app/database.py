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

    for col, coltype, default in [
        ("fps", "REAL", "0.0"),
        ("codec", "TEXT", "''"),
        ("has_audio", "INTEGER", "0"),
        ("file_size", "INTEGER", "0"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE assets ADD COLUMN {col} {coltype} DEFAULT {default}")
        except sqlite3.OperationalError:
            pass

    # Templates table (V1.3: + is_default, bgm_volume, product_scale, product_position, main_video_scale)
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
            is_default INTEGER DEFAULT 0,
            bgm_volume REAL DEFAULT 0.15,
            tts_volume REAL DEFAULT 1.0,
            product_scale REAL DEFAULT 0.25,
            product_position TEXT DEFAULT 'bottom-right',
            main_video_scale REAL DEFAULT 0.4,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (main_video_asset_id) REFERENCES assets(id),
            FOREIGN KEY (background_asset_id) REFERENCES assets(id),
            FOREIGN KEY (product_asset_id) REFERENCES assets(id),
            FOREIGN KEY (bgm_asset_id) REFERENCES assets(id)
        )
    """)

    for col, coltype, default in [
        ("is_default", "INTEGER", "0"),
        ("bgm_volume", "REAL", "0.15"),
        ("tts_volume", "REAL", "1.0"),
        ("product_scale", "REAL", "0.25"),
        ("product_position", "TEXT", "'bottom-right'"),
        ("main_video_scale", "REAL", "0.4"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE templates ADD COLUMN {col} {coltype} DEFAULT {default}")
        except sqlite3.OperationalError:
            pass

    # Projects table (V1.3: keep existing, add asset ID fields)
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

    for col, coltype, default in [
        ("error", "TEXT", "''"),
        ("voice", "TEXT", "''"),
        ("progress", "INTEGER", "0"),
        ("main_video_asset_id", "INTEGER", "NULL"),
        ("background_asset_id", "INTEGER", "NULL"),
        ("product_asset_id", "INTEGER", "NULL"),
        ("bgm_asset_id", "INTEGER", "NULL"),
        ("subtitle_style_json", "TEXT", "'{}'"),
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
    _create_default_templates()
    print(f"[DB] Database initialized at: {DATABASE_PATH}")


def _create_default_templates():
    """Create 3 built-in default templates if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM templates WHERE is_default = 1")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    defaults = [
        {
            "name": "半身口播模板",
            "subtitle_style_json": '{"fontSize":48,"position":"bottom","stroke":2}',
            "layout_json": '{"mainVideoX":30,"mainVideoY":10,"mainVideoW":40,"mainVideoH":50}',
            "main_video_scale": 0.4,
            "bgm_volume": 0.0,
            "product_scale": 0.0,
        },
        {
            "name": "商品介绍模板",
            "subtitle_style_json": '{"fontSize":48,"position":"bottom","stroke":2}',
            "layout_json": '{"mainVideoX":5,"mainVideoY":10,"mainVideoW":50,"mainVideoH":60}',
            "main_video_scale": 0.5,
            "bgm_volume": 0.15,
            "product_scale": 0.2,
        },
        {
            "name": "故事讲述模板",
            "subtitle_style_json": '{"fontSize":36,"position":"middle","stroke":1}',
            "layout_json": '{"mainVideoX":25,"mainVideoY":5,"mainVideoW":50,"mainVideoH":65}',
            "main_video_scale": 0.5,
            "bgm_volume": 0.12,
            "product_scale": 0.0,
        },
    ]

    for tmpl in defaults:
        cursor.execute(
            """INSERT INTO templates
               (name, subtitle_style_json, layout_json, is_default,
                main_video_scale, bgm_volume, product_scale,
                product_position, output_width, output_height)
               VALUES (?, ?, ?, 1, ?, ?, ?, 'bottom-right', 1080, 1920)""",
            (tmpl["name"], tmpl["subtitle_style_json"], tmpl["layout_json"],
             tmpl["main_video_scale"], tmpl["bgm_volume"], tmpl["product_scale"])
        )
    conn.commit()
    conn.close()
    print("[DB] Created 3 default templates")


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