"""
Render Router - Combine assets into final video.
"""
from fastapi import APIRouter, HTTPException
import json

from app.database import get_db_connection
from app.models import RenderRequest, RenderResponse
from app.services.ffmpeg_service import render_video

router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/render")
async def render_final_video(request: RenderRequest):
    """
    Render final video by combining:
    - Background (image or video)
    - Main video (character)
    - TTS audio
    - BGM (low volume)
    - Subtitles
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get asset paths
    main_video_path = None
    background_path = None
    bgm_path = None

    if request.main_video_asset_id:
        cursor.execute("SELECT path FROM assets WHERE id = ?", (request.main_video_asset_id,))
        row = cursor.fetchone()
        if row:
            main_video_path = row["path"]

    if request.background_asset_id:
        cursor.execute("SELECT path FROM assets WHERE id = ?", (request.background_asset_id,))
        row = cursor.fetchone()
        if row:
            background_path = row["path"]

    if request.bgm_asset_id:
        cursor.execute("SELECT path FROM assets WHERE id = ?", (request.bgm_asset_id,))
        row = cursor.fetchone()
        if row:
            bgm_path = row["path"]

    conn.close()

    # Use request fields if provided
    audio_path = request.audio_path
    subtitle_path = request.subtitle_path
    output_width = request.output_width or 1080
    output_height = request.output_height or 1920
    layout_json = request.layout_json

    try:
        output_path, duration = render_video(
            main_video_path=main_video_path,
            background_path=background_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            bgm_path=bgm_path,
            output_path=None,  # Auto-generate
            output_width=output_width,
            output_height=output_height,
            layout_json=layout_json
        )

        # Update project if project_id provided
        if request.project_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE projects SET output_path = ?, status = 'completed' WHERE id = ?",
                (output_path, request.project_id)
            )
            conn.commit()
            conn.close()

        return RenderResponse(
            success=True,
            output_path=output_path,
            duration=duration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video rendering failed: {str(e)}")