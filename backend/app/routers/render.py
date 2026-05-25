"""
Render Router - Video composition with health checks and error handling.
"""
from fastapi import APIRouter, HTTPException
from app.database import get_db_connection
from app.models import RenderRequest, RenderResponse
from app.services.ffmpeg_service import (
    render_video, generate_test_assets, get_ffmpeg_path,
    get_video_info, get_ffprobe_path
)
import os
import subprocess

router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/health")
async def video_health():
    """Check FFmpeg and output directory availability."""
    ffmpeg_ok = False
    ffprobe_ok = False
    output_writable = False

    ffmpeg_path = get_ffmpeg_path()
    try:
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True, timeout=10
        )
        ffmpeg_ok = (result.returncode == 0)
    except Exception:
        pass

    ffprobe_path = get_ffprobe_path()
    try:
        result = subprocess.run(
            [ffprobe_path, "-version"],
            capture_output=True, timeout=10
        )
        ffprobe_ok = (result.returncode == 0)
    except Exception:
        pass

    try:
        test_dir = os.path.join(os.path.dirname(ffmpeg_path), "test_write")
        with open(test_dir, "w") as f:
            f.write("test")
        os.remove(test_dir)
        output_writable = True
    except Exception:
        # Fallback: check outputs dir
        try:
            test_path = os.path.join(os.getcwd(), "outputs", "test_write")
            os.makedirs(os.path.dirname(test_path), exist_ok=True)
            with open(test_path, "w") as f:
                f.write("test")
            os.remove(test_path)
            output_writable = True
        except Exception:
            output_writable = False

    return {
        "ffmpeg": "ok" if ffmpeg_ok else "not_found",
        "ffprobe": "ok" if ffprobe_ok else "not_found",
        "output_writable": output_writable,
        "ffmpeg_path": ffmpeg_path
    }


@router.post("/render")
async def render_final_video(request: RenderRequest):
    """
    Render final video. Simplified V1.1 pipeline:
    main video + TTS audio → MP4
    """
    from app.database import get_setting
    from pathlib import Path

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    output_dir = BASE_DIR / "outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Get asset paths from DB
    main_video_path = None
    background_path = None
    bgm_path = None

    conn = get_db_connection()
    cursor = conn.cursor()

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

    conn.close()

    audio_path = request.audio_path
    subtitle_path = request.subtitle_path
    output_width = request.output_width or 1080
    output_height = request.output_height or 1920

    timeout = 180  # 3 minutes max

    try:
        output_path, duration = render_video(
            main_video_path=main_video_path,
            background_path=background_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            output_path=None,
            output_width=output_width,
            output_height=output_height,
            timeout=timeout,
        )

        if request.project_id:
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute(
                "UPDATE projects SET output_path = ?, status = 'completed' WHERE id = ?",
                (output_path, request.project_id)
            )
            conn2.commit()
            conn2.close()

        return RenderResponse(
            success=True,
            output_path=output_path,
            duration=duration
        )

    except Exception as e:
        error_msg = str(e)
        # Update project status to failed
        if request.project_id:
            try:
                conn3 = get_db_connection()
                cursor3 = conn3.cursor()
                cursor3.execute(
                    "UPDATE projects SET status = 'failed' WHERE id = ?",
                    (request.project_id,)
                )
                conn3.commit()
                conn3.close()
            except Exception:
                pass

        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/render/test")
async def render_test_video():
    """
    Run full pipeline test with auto-generated 10s assets.
    Returns paths to generated test video.
    """
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    output_dir = BASE_DIR / "outputs"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Generate test assets
        assets = generate_test_assets(str(output_dir))

        if not assets.get("main_video") or not assets.get("audio"):
            raise Exception(
                f"Test asset generation failed. "
                f"Generated: {list(assets.keys())}"
            )

        # Run render with test assets
        output_path, duration = render_video(
            main_video_path=assets["main_video"],
            audio_path=assets["audio"],
            output_width=1080,
            output_height=1920,
            timeout=180,
        )

        return {
            "success": True,
            "test_video": output_path,
            "duration": duration,
            "message": "Test render completed successfully within timeout"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test render failed: {str(e)}"
        )