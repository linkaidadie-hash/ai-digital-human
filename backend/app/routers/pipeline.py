"""
Pipeline Router V1.2 - Unified video generation pipeline.
TTS + Subtitle + Full FFmpeg composition in one call.
"""
import os
import time
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.database import get_db_connection

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def update_project(project_id: int, **kwargs):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for key, value in kwargs.items():
            cursor.execute(f"UPDATE projects SET {key} = ? WHERE id = ?", (str(value), project_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Pipeline] update_project error: {e}")


def run_pipeline_bg(
    project_id: int,
    script_text: str,
    voice: str,
    main_video_asset_id: int,
    background_asset_id: int,
    product_asset_id: int,
    bgm_asset_id: int,
    output_width: int,
    output_height: int,
    subtitle_font_size: int,
    subtitle_position: str,
    subtitle_stroke: int,
    bgm_volume: float,
    product_position: str,
    product_scale: float,
):
    from app.services.ffmpeg_service import (
        log as ffmpeg_log, detect_media, loop_or_trim,
        render_video_v12, clear_log,
    )
    from app.services.tts_service import generate_tts
    from app.services.subtitle_service import generate_subtitles

    log = ffmpeg_log
    clear_log()
    log(f"[Pipeline V1.2] Starting for project {project_id}")

    update_project(project_id, status="processing", progress=5)

    try:
        # ── 1. TTS ──────────────────────────────────────────────────────────
        update_project(project_id, status="processing", progress=10)
        log("[Pipeline] Step 1/5: Generating TTS...")
        audio_path, audio_duration = generate_tts(text=script_text, voice=voice)
        update_project(project_id, audio_path=audio_path, progress=25)
        log(f"[Pipeline] TTS done: {audio_path} ({audio_duration:.1f}s)")

        # ── 2. Subtitle ──────────────────────────────────────────────────────
        update_project(project_id, status="processing", progress=30)
        log("[Pipeline] Step 2/5: Generating subtitles...")
        subtitle_path, seg_count = generate_subtitles(text=script_text, duration=audio_duration)
        update_project(project_id, subtitle_path=subtitle_path, progress=40)
        log(f"[Pipeline] Subtitles done: {subtitle_path} ({seg_count} segs)")

        # ── 3. Resolve asset paths ────────────────────────────────────────────
        def get_asset_path(asset_id) -> str:
            if not asset_id:
                return None
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM assets WHERE id = ?", (asset_id,))
            row = cursor.fetchone()
            conn.close()
            return row["path"] if row else None

        main_video_path = get_asset_path(main_video_asset_id)
        background_path = get_asset_path(background_asset_id)
        product_path = get_asset_path(product_asset_id)
        bgm_path = get_asset_path(bgm_asset_id)

        log(f"[Pipeline] Assets — main={main_video_path}, bg={background_path}, "
            f"product={product_path}, bgm={bgm_path}")

        # ── 4. Render video ────────────────────────────────────────────────────
        update_project(project_id, status="processing", progress=50)
        log("[Pipeline] Step 3/5: Rendering video...")

        # Get TTS duration from audio
        if audio_path:
            media = detect_media(audio_path)
            target_dur = media.get("duration", audio_duration)
        else:
            target_dur = 10.0

        output_path, video_duration = render_video_v12(
            tts_audio_path=audio_path,
            target_duration=target_dur,
            main_video_path=main_video_path,
            background_path=background_path,
            product_path=product_path,
            product_position=product_position or "bottom-right",
            product_scale=product_scale if product_scale else 0.25,
            bgm_path=bgm_path,
            bgm_volume=bgm_volume if bgm_volume else 0.15,
            tts_volume=1.0,
            subtitle_path=subtitle_path,
            subtitle_font_size=subtitle_font_size if subtitle_font_size else 48,
            subtitle_position=subtitle_position or "bottom",
            subtitle_stroke=subtitle_stroke if subtitle_stroke else 2,
            output_width=output_width or 1080,
            output_height=output_height or 1920,
            timeout=180,
        )

        update_project(project_id, progress=95)
        log(f"[Pipeline] Render done: {output_path} ({video_duration:.1f}s)")

        # ── 5. Complete ──────────────────────────────────────────────────────
        update_project(project_id, status="completed", output_path=output_path, progress=100)
        log(f"[Pipeline V1.2] COMPLETE for project {project_id}")

    except Exception as e:
        log(f"[Pipeline V1.2] FAILED for project {project_id}: {e}")
        update_project(project_id, status="failed", error=str(e), progress=0)


@router.post("/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    template_id: int = None,
    script: str = "",
    voice: str = "zh-CN-XiaoxiaoNeural",
    # Asset IDs
    main_video_asset_id: int = None,
    background_asset_id: int = None,
    product_asset_id: int = None,
    bgm_asset_id: int = None,
    # Output
    output_width: int = 1080,
    output_height: int = 1920,
    # Subtitle style
    subtitle_font_size: int = 48,
    subtitle_position: str = "bottom",
    subtitle_stroke: int = 2,
    # Audio
    bgm_volume: float = 0.15,
    # Product overlay
    product_position: str = "bottom-right",
    product_scale: float = 0.25,
):
    """Run the full V1.2 pipeline: TTS → subtitles → full composition."""
    if not script or not script.strip():
        raise HTTPException(status_code=400, detail="文案不能为空")

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

    background_tasks.add_task(
        run_pipeline_bg,
        project_id, script, voice,
        main_video_asset_id, background_asset_id,
        product_asset_id, bgm_asset_id,
        output_width, output_height,
        subtitle_font_size, subtitle_position, subtitle_stroke,
        bgm_volume, product_position, product_scale,
    )

    return {
        "success": True,
        "project_id": project_id,
        "message": "Pipeline started. Poll GET /api/pipeline/status/{project_id} for progress."
    }


@router.get("/status/{project_id}")
async def get_pipeline_status(project_id: int):
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
    """V1.2 acceptance test with synthetic 10s assets."""
    from app.services.ffmpeg_service import generate_test_assets, render_video_v12, detect_media

    output_dir = BASE_DIR / "outputs"
    os.makedirs(output_dir, exist_ok=True)

    start = time.time()
    assets = generate_test_assets(str(output_dir))

    if not assets.get("main_video") or not assets.get("audio"):
        raise HTTPException(status_code=500, detail=f"Test asset generation failed")

    # Get audio duration as target
    info = detect_media(assets["audio"])
    dur = info.get("duration", 10.0)

    output_path, video_duration = render_video_v12(
        tts_audio_path=assets["audio"],
        target_duration=dur,
        main_video_path=assets["main_video"],
        background_path=assets.get("background"),
        subtitle_path=None,
        output_width=1080,
        output_height=1920,
        timeout=180,
    )

    elapsed = time.time() - start
    size_kb = os.path.getsize(output_path) / 1024

    return {
        "success": True,
        "test_video": output_path,
        "duration": video_duration,
        "elapsed_seconds": round(elapsed, 1),
        "size_kb": round(size_kb, 0),
        "status": "PASS" if elapsed < 60 else "SLOW",
    }