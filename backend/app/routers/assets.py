"""
Assets Router - Import and list media assets.
"""
import os
import shutil
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
from pathlib import Path

from app.database import get_db_connection
from app.models import AssetCreate, AssetResponse
from app.services.ffmpeg_service import get_video_info

router = APIRouter(prefix="/api/assets", tags=["assets"])

# Asset type to directory mapping
ASSET_DIRS = {
    "character_video": "character_videos",
    "action_video": "action_videos",
    "background": "backgrounds",
    "product": "products",
    "bgm": "bgm",
    "font": "fonts"
}


@router.post("/import")
async def import_asset(
    file: UploadFile = File(...),
    name: str = "",
    asset_type: str = "character_video",
    tags: str = ""
):
    """
    Import a media asset file into the system.
    The file is copied to the appropriate assets directory.
    """
    if asset_type not in ASSET_DIRS:
        raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")

    # Determine target directory
    backend_dir = Path(__file__).resolve().parent.parent.parent
    target_dir = backend_dir / "assets" / ASSET_DIRS[asset_type]

    # Generate filename
    original_name = file.filename or "unknown"
    if not name:
        name = original_name.rsplit(".", 1)[0]  # Use filename without extension

    # Unique filename
    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "mp4"
    import time
    unique_name = f"{name}_{int(time.time() * 1000)}.{ext}"
    target_path = target_dir / unique_name

    # Copy file to target directory
    try:
        async with aiofiles.open(target_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get media info (duration, width, height)
    duration = 0.0
    width = 0
    height = 0

    try:
        info = get_video_info(str(target_path))
        duration = info.get("duration", 0)
        width = info.get("width", 0)
        height = info.get("height", 0)
    except Exception:
        pass  # Non-video files may not have ffprobe info

    # Save to database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO assets (name, type, path, tags, duration, width, height)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (name, asset_type, str(target_path), tags, duration, width, height)
    )
    asset_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "success": True,
        "asset_id": asset_id,
        "path": str(target_path),
        "duration": duration,
        "width": width,
        "height": height
    }


@router.get("")
async def list_assets(type: Optional[str] = None):
    """List all assets, optionally filtered by type."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if type:
        cursor.execute(
            "SELECT * FROM assets WHERE type = ? ORDER BY created_at DESC",
            (type,)
        )
    else:
        cursor.execute("SELECT * FROM assets ORDER BY created_at DESC")

    rows = cursor.fetchall()
    conn.close()

    assets = [dict(row) for row in rows]
    return {"assets": assets, "count": len(assets)}


@router.delete("/{asset_id}")
async def delete_asset(asset_id: int):
    """Delete an asset and its file."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT path FROM assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found")

    file_path = row["path"]

    # Delete file
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete from database
    cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()

    return {"success": True, "deleted_id": asset_id}