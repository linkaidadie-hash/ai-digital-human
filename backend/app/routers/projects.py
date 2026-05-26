"""
Projects Router - CRUD for video projects + copy.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import json

from app.database import get_db_connection

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
async def create_project(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO projects
               (name, template_id, script_text, voice, audio_path, subtitle_path,
                output_path, status, main_video_asset_id, background_asset_id,
                product_asset_id, bgm_asset_id, subtitle_style_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("name", ""),
                data.get("templateId"),
                data.get("script", ""),
                data.get("voice", ""),
                data.get("audioPath", ""),
                data.get("subtitlePath", ""),
                data.get("outputPath", ""),
                data.get("status", "draft"),
                data.get("mainVideoAssetId"),
                data.get("backgroundAssetId"),
                data.get("productAssetId"),
                data.get("bgmAssetId"),
                data.get("subtitleStyleJson", "{}"),
            )
        )
        project_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"success": True, "project_id": project_id}


@router.get("")
async def list_projects(status: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC",
            (status,)
        )
    else:
        cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return {"projects": [dict(row) for row in rows], "count": len(rows)}


@router.get("/{project_id}")
async def get_project(project_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="项目不存在")
    result = dict(row)
    print(f"[Projects] GET /{project_id} -> status={result.get('status')} progress={result.get('progress')}")
    return result


@router.get("/{project_id}/status")
async def get_project_status(project_id: int):
    return await get_project(project_id)


@router.put("/{project_id}")
async def update_project(project_id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE projects SET
           name = ?, template_id = ?, script_text = ?, voice = ?,
           audio_path = ?, subtitle_path = ?, output_path = ?, status = ?,
           main_video_asset_id = ?, background_asset_id = ?,
           product_asset_id = ?, bgm_asset_id = ?, subtitle_style_json = ?
           WHERE id = ?""",
        (
            data.get("name"),
            data.get("templateId"),
            data.get("script", ""),
            data.get("voice", ""),
            data.get("audioPath", ""),
            data.get("subtitlePath", ""),
            data.get("outputPath", ""),
            data.get("status", "draft"),
            data.get("mainVideoAssetId"),
            data.get("backgroundAssetId"),
            data.get("productAssetId"),
            data.get("bgmAssetId"),
            data.get("subtitleStyleJson", "{}"),
            project_id,
        )
    )
    conn.commit()
    conn.close()
    return {"success": True, "project_id": project_id}


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return {"success": True, "deleted_id": project_id}


@router.post("/{project_id}/copy")
async def copy_project(project_id: int):
    """Duplicate a project as a new draft."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="项目不存在")
    p = dict(row)
    import time
    new_name = (p.get("name") or "项目") + " (副本)"
    cursor.execute(
        """INSERT INTO projects
           (name, template_id, script_text, voice, audio_path, subtitle_path,
            output_path, status, main_video_asset_id, background_asset_id,
            product_asset_id, bgm_asset_id, subtitle_style_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?)""",
        (
            new_name,
            p.get("template_id"),
            p.get("script_text", ""),
            p.get("voice", ""),
            "", "", "",  # clear outputs
            p.get("main_video_asset_id"),
            p.get("background_asset_id"),
            p.get("product_asset_id"),
            p.get("bgm_asset_id"),
            p.get("subtitle_style_json", "{}"),
        )
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "project_id": new_id, "name": new_name}