"""
Assets Router V1.2 - Import, detect, preprocess, and list media assets.
"""
import os
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from pathlib import Path

from app.database import get_db_connection
from app.models import AssetCreate, AssetResponse
from app.services.ffmpeg_service import detect_media, validate_format, preprocess_video, preprocess_audio, log as ffmpeg_log

router = APIRouter(prefix="/api/assets", tags=["assets"])

ASSET_DIRS = {
    "character_video": "character_videos",
    "action_video": "action_videos",
    "background": "backgrounds",
    "product": "products",
    "bgm": "bgm",
    "font": "fonts"
}

SUPPORTED_EXTS = {".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png", ".mp3", ".wav", ".webp"}


@router.post("/import")
async def import_asset(
    file: UploadFile = File(...),
    name: str = "",
    asset_type: str = "character_video",
    tags: str = ""
):
    """
    Import a media asset:
    1. Validate format (reject unsupported extensions with friendly message)
    2. Copy to assets directory
    3. Detect media info (duration, resolution, fps, codec, has_audio)
    4. Auto-preprocess video/audio to standard format
    5. Save to database
    """
    if asset_type not in ASSET_DIRS:
        raise HTTPException(status_code=400, detail=f"无效的素材类型：{asset_type}")

    original_name = file.filename or "unknown"
    ext = Path(original_name).suffix.lower()

    if ext not in SUPPORTED_EXTS:
        supported = sorted(set(e for e in SUPPORTED_EXTS if e != ".webp"))
        msg = f"不支持的文件格式「{ext}」，支持：{', '.join(supported)}"
        raise HTTPException(status_code=400, detail=msg)

    backend_dir = Path(__file__).resolve().parent.parent.parent
    target_dir = backend_dir / "assets" / ASSET_DIRS[asset_type]
    os.makedirs(target_dir, exist_ok=True)

    if not name:
        name = original_name.rsplit(".", 1)[0]

    unique_name = f"{name}_{int(time.time() * 1000)}{ext}"
    target_path = target_dir / unique_name

    # Read + write
    try:
        content = await file.read()
        with open(target_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败：{str(e)}")

    # Detect media info
    media_info = detect_media(str(target_path))

    # Auto-preprocess
    is_video = ext in (".mp4", ".mov", ".webm")
    is_audio = ext in (".mp3", ".wav")

    try:
        if is_video:
            processed = preprocess_video(str(target_path))
            if processed != str(target_path):
                # Replace with preprocessed file
                new_path = processed
                media_info = detect_media(new_path)
                log(f"[Asset] Video preprocessed: {target_path.name} → {Path(new_path).name}")
        elif is_audio:
            processed = preprocess_audio(str(target_path))
            if processed != str(target_path):
                new_path = processed
                media_info = detect_media(new_path)
                log(f"[Asset] Audio preprocessed: {target_path.name} → {Path(new_path).name}")
    except Exception as e:
        log(f"[Asset] Preprocess warning: {e}")

    # Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO assets (name, type, path, tags, duration, width, height)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, asset_type, str(target_path), tags,
         media_info.get("duration", 0),
         media_info.get("width", 0),
         media_info.get("height", 0))
    )
    asset_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "asset_id": asset_id,
        "path": str(target_path),
        "duration": round(media_info.get("duration", 0), 2),
        "width": media_info.get("width", 0),
        "height": media_info.get("height", 0),
        "fps": media_info.get("fps", 0),
        "codec": media_info.get("codec", ""),
        "has_audio": media_info.get("has_audio", False),
        "format": media_info.get("format", ext.lstrip(".")),
        "file_size_kb": round(media_info.get("file_size", 0) / 1024, 1),
    }


@router.get("")
async def list_assets(type: Optional[str] = None):
    """List all assets, optionally filtered by type."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if type:
        cursor.execute("SELECT * FROM assets WHERE type = ? ORDER BY created_at DESC", (type,))
    else:
        cursor.execute("SELECT * FROM assets ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"assets": [dict(row) for row in rows], "count": len(rows)}


@router.get("/{asset_id}")
async def get_asset(asset_id: int):
    """Get single asset with full media info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="素材不存在")
    info = dict(row)
    # Enrich with fresh ffprobe data
    path = info.get("path", "")
    if path and os.path.exists(path):
        media = detect_media(path)
        info["fps"] = media.get("fps", 0)
        info["codec"] = media.get("codec", "")
        info["has_audio"] = media.get("has_audio", False)
        info["format"] = media.get("format", "")
        info["file_size_kb"] = round(media.get("file_size", 0) / 1024, 1)
    return info


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete an asset and its file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="素材不存在")
    file_path = row["path"]
    if os.path.exists(file_path):
        os.remove(file_path)
    cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()
    return {"success": True, "deleted_id": asset_id}