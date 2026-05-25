"""
Templates Router - CRUD for video templates.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import json

from app.database import get_db_connection
from app.models import TemplateCreate, TemplateResponse

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.post("")
async def create_template(template: TemplateCreate):
    """Create a new video template."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO templates
               (name, main_video_asset_id, background_asset_id, product_asset_id,
                bgm_asset_id, subtitle_style_json, layout_json, output_width, output_height)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                template.name,
                template.main_video_asset_id,
                template.background_asset_id,
                template.product_asset_id,
                template.bgm_asset_id,
                template.subtitle_style_json,
                template.layout_json,
                template.output_width,
                template.output_height
            )
        )
        template_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    conn.close()

    return {
        "success": True,
        "template_id": template_id,
        "message": f"Template '{template.name}' created"
    }


@router.get("")
async def list_templates():
    """List all templates."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    templates = [dict(row) for row in rows]

    # Parse JSON fields
    for t in templates:
        try:
            if isinstance(t.get("subtitle_style_json"), str):
                t["subtitle_style_json"] = json.loads(t["subtitle_style_json"])
            if isinstance(t.get("layout_json"), str):
                t["layout_json"] = json.loads(t["layout_json"])
        except (json.JSONDecodeError, TypeError):
            pass

    return {"templates": templates, "count": len(templates)}


@router.get("/{template_id}")
async def get_template(template_id: int):
    """Get a specific template by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Template not found")

    template = dict(row)

    # Parse JSON fields
    try:
        if isinstance(template.get("subtitle_style_json"), str):
            template["subtitle_style_json"] = json.loads(template["subtitle_style_json"])
        if isinstance(template.get("layout_json"), str):
            template["layout_json"] = json.loads(template["layout_json"])
    except (json.JSONDecodeError, TypeError):
        pass

    return template


@router.put("/{template_id}")
async def update_template(template_id: int, template: TemplateCreate):
    """Update an existing template."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """UPDATE templates SET
           name = ?, main_video_asset_id = ?, background_asset_id = ?,
           product_asset_id = ?, bgm_asset_id = ?, subtitle_style_json = ?,
           layout_json = ?, output_width = ?, output_height = ?
           WHERE id = ?""",
        (
            template.name,
            template.main_video_asset_id,
            template.background_asset_id,
            template.product_asset_id,
            template.bgm_asset_id,
            template.subtitle_style_json,
            template.layout_json,
            template.output_width,
            template.output_height,
            template_id
        )
    )
    conn.commit()
    conn.close()

    return {"success": True, "template_id": template_id}


@router.delete("/{template_id}")
async def delete_template(template_id: int):
    """Delete a template."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()

    return {"success": True, "deleted_id": template_id}