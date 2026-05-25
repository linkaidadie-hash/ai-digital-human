"""
Pipeline Router - Unified video generation pipeline (V1.1).
TTS + Subtitle + FFmpeg render in one call.
"""
import os
import time
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.database import get_db_connection

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def update_project(project_id: int, **kwargs):
    """Update project fields."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for key, value in kwargs.items():
            cursor.execute(f"UPDATE projects SET {key} = ? WHERE id = ?", (str(value), project_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Pipeline] update_project error: {e}")


def run_pipeline_bg(project_id: int, script_text: str, voice: str,
                    main_video_asset_id: int, output_width: int, output_height: int):
    """
    Run the full pipeline in a background thread.
    Updates project status/progress at each step.
    """
    from app.services.ffmpeg_service import log as ffmpeg_log, render_video
    from app.services.tts_service import generate_tts
    from app.services.subtitle_service import generate_subtitles

    log = ffmpeg_log
    log(f"[Pipeline] Starting background pipeline for project {project_id}")

    # Step 0: Set status to processing
    update_project(project_id, status="processing", progress=5)

    try:
        # Step 1: Generate TTS
        update_project(project_id, status="processing", progress=10)
        log(f"[Pipeline] Step 1/3: Generating TTS...")
        audio_path, audio_duration = generate_tts(
            text=script_text,
            voice=voice or "zh-CN-XiaoxiaoNeural"
        )
        update_project(project_id, audio_path=audio_path, progress=30)
        log(f"[Pipeline] TTS done: {audio_path} ({audio_duration:.1f}s)")

        # Step 2: Generate subtitles
        update_project(project_id, status="processing", progress=35)
        log(f"[Pipeline] Step 2/3: Generating subtitles...")
        subtitle_path, seg_count = generate_subtitles(
            text=script_text,
            duration=audio_duration
        )
        update_project(project_id, subtitle_path=subtitle_path, progress=50)
        log(f"[Pipeline] Subtitles done: {subtitle_path} ({seg_count} segments)")

        # Step 3: Get main video asset path
        main_video_path = None
        if main_video_asset_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM assets WHERE id = ?", (main_video_asset_id,))
            row = cursor.fetchone()
            if row:
                main_video_path = row["path"]
            conn.close()

        # Step 4: Render video
        update_project(project_id, status="processing", progress=55)
        log(f"[Pipeline] Step 3/3: Rendering video...")
        output_path, video_duration = render_video(
            main_video_path=main_video_path,
            audio_path=audio_path,
            subtitle_path=None,  # V1.1: skip subtitle burn-in for speed
            output_width=output_width or 1080,
            output_height=output_height or 1920,
            timeout=180
        )
        update_project(project_id, progress=95)
        log(f"[Pipeline] Render done: {output_path} ({video_duration:.1f}s)")

        # Final: Mark complete
        update_project(project_id, status="completed", output_path=output_path, progress=100)
        log(f"[Pipeline] Pipeline COMPLETE for project {project_id}")

    except Exception as e:
        log(f"[Pipeline] Pipeline FAILED for project {project_id}: {e}")
        update_project(project_id, status="failed", error=str(e), progress=0)


@router.post("/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    template_id: int = None,
    script: str = "",
    voice: str = "zh-CN-XiaoxiaoNeural",
    main_video_asset_id: int = None,
    output_width: int = 1080,
    output_height: int = 1920
):
    """
    Run the full video generation pipeline:
    1. Generate TTS audio
    2. Generate SRT subtitles
    3. Render final MP4 video

    Returns immediately after spawning the background job.
    Poll GET /api/pipeline/status/{project_id} for progress.
    """
    if not script or len(script.strip()) == 0:
        raise HTTPException(status_code=400, detail="Script text cannot be empty")

    # Create project in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO projects (name, template_id, script_text, voice, status, progress)
           VALUES (?, ?, ?, ?, 'pending', 0)""",
        (f"视频_{int(time.time())}", template_id, script, voice)
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Spawn background pipeline
    background_tasks.add_task(
        run_pipeline_bg,
        project_id,
        script,
        voice,
        main_video_asset_id,
        output_width,
        output_height
    )

    return {
        "success": True,
        "project_id": project_id,
        "message": "Pipeline started. Poll GET /api/pipeline/status/{project_id} for progress."
    }


@router.get("/status/{project_id}")
async def get_pipeline_status(project_id: int):
    """Get current pipeline status and progress."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    return dict(row)


@router.post("/render/test")
async def render_test():
    """
    V1.1 acceptance test: generate 10s test video with synthetic assets.
    Target: completes within 60 seconds.
    """
    from app.services.ffmpeg_service import generate_test_assets, render_video

    output_dir = BASE_DIR / "outputs"
    os.makedirs(output_dir, exist_ok=True)

    start = time.time()
    try:
        assets = generate_test_assets(str(output_dir))

        if not assets.get("main_video") or not assets.get("audio"):
            raise HTTPException(
                status_code=500,
                detail=f"Test asset generation failed: {list(assets.keys())}"
            )

        output_path, duration = render_video(
            main_video_path=assets["main_video"],
            audio_path=assets["audio"],
            output_width=1080,
            output_height=1920,
            timeout=180
        )

        elapsed = time.time() - start
        size_kb = os.path.getsize(output_path) / 1024

        return {
            "success": True,
            "test_video": output_path,
            "duration": duration,
            "elapsed_seconds": round(elapsed, 1),
            "size_kb": round(size_kb, 0),
            "status": "PASS" if elapsed < 60 else "SLOW",
            "message": f"Test render completed in {elapsed:.1f}s {'(PASS)' if elapsed < 60 else '(SLOW - target 60s)'}"
        }

    except Exception as e:
        elapsed = time.time() - start
        raise HTTPException(
            status_code=500,
            detail=f"Test render failed after {elapsed:.1f}s: {str(e)}"
        )