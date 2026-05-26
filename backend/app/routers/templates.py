"""
Templates Router - CRUD for video templates + copy + default templates.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import json

from app.database import get_db_connection

router = APIRouter(prefix="/api/templates", tags=["templates"])


def _parse_template(row: dict) -> dict:
    tmpl = dict(row)
    for field in ("subtitle_style_json", "layout_json"):
        try:
            val = tmpl.get(field)
            if isinstance(val, str):
                tmpl[field] = json.loads(val)
            elif val is None:
                tmpl[field] = {}
        except (json.JSONDecodeError, TypeError):
            tmpl[field] = {}
    return tmpl


@router.post("")
async def create_template(data: dict):
    """Create a new video template."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO templates
               (name, main_video_asset_id, background_asset_id, product_asset_id,
                bgm_asset_id, subtitle_style_json, layout_json,
                output_width, output_height, is_default,
                bgm_volume, tts_volume, product_scale, product_position, main_video_scale)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("name", ""),
                data.get("mainVideoAssetId"),
                data.get("backgroundAssetId"),
                data.get("productAssetId"),
                data.get("bgmAssetId"),
                data.get("subtitleStyleJson", "{}"),
                data.get("layoutJson", "{}"),
                data.get("outputWidth", 1080),
                data.get("outputHeight", 1920),
                0,
                data.get("bgmVolume", 0.15),
                data.get("ttsVolume", 1.0),
                data.get("productScale", 0.25),
                data.get("productPosition", "bottom-right"),
                data.get("mainVideoScale", 0.4),
            )
        )
        template_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"success": True, "template_id": template_id}


@router.get("")
async def list_templates():
    """List all templates (including defaults)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates ORDER BY is_default DESC, created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    templates = [_parse_template(dict(row)) for row in rows]
    return {"templates": templates, "count": len(templates)}


@router.get("/{template_id}")
async def get_template(template_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="模板不存在")
    return _parse_template(dict(row))


@router.put("/{template_id}")
async def update_template(template_id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE templates SET
           name = ?, main_video_asset_id = ?, background_asset_id = ?,
           product_asset_id = ?, bgm_asset_id = ?,
           subtitle_style_json = ?, layout_json = ?,
           output_width = ?, output_height = ?,
           bgm_volume = ?, tts_volume = ?,
           product_scale = ?, product_position = ?, main_video_scale = ?
           WHERE id = ?""",
        (
            data.get("name", ""),
            data.get("mainVideoAssetId"),
            data.get("backgroundAssetId"),
            data.get("productAssetId"),
            data.get("bgmAssetId"),
            data.get("subtitleStyleJson", "{}"),
            data.get("layoutJson", "{}"),
            data.get("outputWidth", 1080),
            data.get("outputHeight", 1920),
            data.get("bgmVolume", 0.15),
            data.get("ttsVolume", 1.0),
            data.get("productScale", 0.25),
            data.get("productPosition", "bottom-right"),
            data.get("mainVideoScale", 0.4),
            template_id,
        )
    )
    conn.commit()
    conn.close()
    return {"success": True, "template_id": template_id}


@router.delete("/{template_id}")
async def delete_template(template_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Prevent deleting default templates
    cursor.execute("SELECT is_default FROM templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    if row and row["is_default"]:
        conn.close()
        raise HTTPException(status_code=403, detail="默认模板不能删除")
    cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return {"success": True, "deleted_id": template_id}


@router.post("/{template_id}/copy")
async def copy_template(template_id: int):
    """Create a copy of an existing template."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="模板不存在")

    tmpl = dict(row)
    # Rename copy
    copy_name = tmpl["name"] + " (副本)"
    cursor.execute(
        """INSERT INTO templates
           (name, main_video_asset_id, background_asset_id, product_asset_id,
            bgm_asset_id, subtitle_style_json, layout_json,
            output_width, output_height, is_default,
            bgm_volume, tts_volume, product_scale, product_position, main_video_scale)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)""",
        (
            copy_name,
            tmpl.get("main_video_asset_id"),
            tmpl.get("background_asset_id"),
            tmpl.get("product_asset_id"),
            tmpl.get("bgm_asset_id"),
            tmpl.get("subtitle_style_json", "{}"),
            tmpl.get("layout_json", "{}"),
            tmpl.get("output_width", 1080),
            tmpl.get("output_height", 1920),
            tmpl.get("bgm_volume", 0.15),
            tmpl.get("tts_volume", 1.0),
            tmpl.get("product_scale", 0.25),
            tmpl.get("product_position", "bottom-right"),
            tmpl.get("main_video_scale", 0.4),
        )
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "template_id": new_id, "name": copy_name}