"""
Projects Router - CRUD for video projects.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.database import get_db_connection
from app.models import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("")
async def create_project(project: ProjectCreate):
    """Create a new video project."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """INSERT INTO projects
               (name, template_id, script_text, audio_path, subtitle_path, output_path, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                project.name,
                project.template_id,
                project.script_text,
                project.audio_path,
                project.subtitle_path,
                project.output_path,
                project.status or "draft"
            )
        )
        project_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

    conn.close()

    return {
        "success": True,
        "project_id": project_id,
        "message": f"Project '{project.name}' created"
    }


@router.get("")
async def list_projects(status: Optional[str] = None):
    """List all projects, optionally filtered by status."""
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

    projects = [dict(row) for row in rows]
    return {"projects": projects, "count": len(projects)}


@router.get("/{project_id}")
async def get_project(project_id: int):
    """Get a specific project by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return dict(row)


@router.get("/{project_id}/status")
async def get_project_status(project_id: int):
    """Get project status and progress (used by polling)."""
    return await get_project(project_id)


@router.put("/{project_id}")
async def update_project(project_id: int, project: ProjectCreate):
    """Update an existing project."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """UPDATE projects SET
           name = ?, template_id = ?, script_text = ?, audio_path = ?,
           subtitle_path = ?, output_path = ?, status = ?
           WHERE id = ?""",
        (
            project.name,
            project.template_id,
            project.script_text,
            project.audio_path,
            project.subtitle_path,
            project.output_path,
            project.status or "draft",
            project_id
        )
    )
    conn.commit()
    conn.close()

    return {"success": True, "project_id": project_id}


@router.delete("/{project_id}")
async def delete_project(project_id: int):
    """Delete a project."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

    return {"success": True, "deleted_id": project_id}