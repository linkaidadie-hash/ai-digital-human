"""
Pipeline Router V1.3 - Unified video generation pipeline.
Loads full config from template + script + layout parameters.
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


def _get_template(template_id: int) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM templates WHERE id = ?", (template_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    tmpl = dict(row)
    for f in ("subtitle_style_json", "layout_json"):
        try:
            val = tmpl.get(f)
            if isinstance(val, str):
                tmpl[f] = json.loads(val) if val else {}
        except Exception:
            tmpl[f] = {}
    return tmpl


def _get_asset_path(asset_id) -> str:
    if not asset_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()
    conn.close()
    return row["path"] if row else None


def run_pipeline_bg(
    project_id: int,
    script_text: str,
    voice: str,
    template_id: int,
    # Override values (from generate page)
    main_video_asset_id: int,
    background_asset_id: int,
    product_asset_id: int,
    bgm_asset_id: int,
    main_video_scale: float,
    product_scale: float,
    product_position: str,
    bgm_volume: float,
    subtitle_font_size: int,
    subtitle_position: str,
    subtitle_stroke: int,
    main_video_x: int,
    main_video_y: int,
    output_width: int,
    output_height: int,
):
    from app.services.ffmpeg_service import (
        log as ffmpeg_log, detect_media, loop_or_trim, render_video_v12, clear_log,
    )
    from app.services.tts_service import generate_tts
    from app.services.subtitle_service import generate_subtitles

    log = ffmpeg_log
    clear_log()
    log(f"[Pipeline V1.3] Starting for project {project_id}")

    update_project(project_id, status="processing", progress=5)

    try:
        # ── 1. TTS ──────────────────────────────────────────────────────────
        update_project(project_id, status="processing", progress=10)
        log("[Pipeline] Step 1/4: Generating TTS...")
        audio_path, audio_duration = generate_tts(text=script_text, voice=voice)
        update_project(project_id, audio_path=audio_path, progress=25)
        log(f"[Pipeline] TTS done: {audio_path} ({audio_duration:.1f}s)")

        # ── 2. Subtitle ──────────────────────────────────────────────────────
        update_project(project_id, status="processing", progress=30)
        log("[Pipeline] Step 2/4: Generating subtitles...")
        subtitle_path, seg_count = generate_subtitles(text=script_text, duration=audio_duration)
        update_project(project_id, subtitle_path=subtitle_path, progress=40)
        log(f"[Pipeline] Subtitles done: {subtitle_path} ({seg_count} segs)")

        # ── 3. Resolve asset paths ────────────────────────────────────────────
        main_video_path = _get_asset_path(main_video_asset_id)
        background_path = _get_asset_path(background_asset_id)
        product_path = _get_asset_path(product_asset_id)
        bgm_path = _get_asset_path(bgm_asset_id)

        log(f"[Pipeline] Assets — main={main_video_path}, bg={background_path}, "
            f"product={product_path}, bgm={bgm_path}")

        # ── 4. Render ────────────────────────────────────────────────────────
        update_project(project_id, status="processing", progress=50)
        log("[Pipeline] Step 3/4: Rendering video...")

        target_dur = audio_duration
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
        log(f"[Pipeline V1.3] COMPLETE for project {project_id}")

    except Exception as e:
        log(f"[Pipeline V1.3] FAILED: {e}")
        update_project(project_id, status="failed", error=str(e), progress=0)


@router.post("/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    template_id: int = None,
    script: str = "",
    voice: str = "zh-CN-XiaoxiaoNeural",
    # All V1.3 params (from template or override)
    main_video_asset_id: int = None,
    background_asset_id: int = None,
    product_asset_id: int = None,
    bgm_asset_id: int = None,
    # Layout & style
    main_video_scale: float = 0.4,
    product_scale: float = 0.25,
    product_position: str = "bottom-right",
    bgm_volume: float = 0.15,
    subtitle_font_size: int = 48,
    subtitle_position: str = "bottom",
    subtitle_stroke: int = 2,
    main_video_x: int = 30,
    main_video_y: int = 10,
    output_width: int = 1080,
    output_height: int = 1920,
):
    """Run full pipeline. Loads template defaults, then applies overrides."""
    if not script or not script.strip():
        raise HTTPException(status_code=400, detail="文案不能为空")

    # Load template to fill in missing params
    tmpl = {}
    if template_id:
        tmpl = _get_template(template_id)

    # Apply template defaults for any param not explicitly provided
    def v(val, default):
        return val if val is not None else default

    # Resolve asset IDs (override wins)
    mv_id = main_video_asset_id if main_video_asset_id else tmpl.get("main_video_asset_id")
    bg_id = background_asset_id if background_asset_id else tmpl.get("background_asset_id")
    prod_id = product_asset_id if product_asset_id else tmpl.get("product_asset_id")
    bgm_id = bgm_asset_id if bgm_asset_id else tmpl.get("bgm_asset_id")

    # Layout
    layout = tmpl.get("layout_json") or {}
    subtitle_style = tmpl.get("subtitle_style_json") or {}

    # Scale & position
    mv_scale = main_video_scale if main_video_scale != 0.4 else tmpl.get("main_video_scale", 0.4)
    prod_scale = product_scale if product_scale != 0.25 else tmpl.get("product_scale", 0.25)
    prod_pos = product_position if product_position != "bottom-right" else tmpl.get("product_position", "bottom-right")
    bvol = bgm_volume if bgm_volume != 0.15 else tmpl.get("bgm_volume", 0.15)

    sub_fs = subtitle_font_size if subtitle_font_size != 48 else subtitle_style.get("fontSize", 48)
    sub_pos = subtitle_position if subtitle_position != "bottom" else subtitle_style.get("position", "bottom")
    sub_st = subtitle_stroke if subtitle_stroke != 2 else subtitle_style.get("stroke", 2)

    mv_x = main_video_x if main_video_x != 30 else layout.get("mainVideoX", 30)
    mv_y = main_video_y if main_video_y != 10 else layout.get("mainVideoY", 10)

    out_w = output_width or tmpl.get("output_width", 1080)
    out_h = output_height or tmpl.get("output_height", 1920)

    # Create project
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO projects
           (name, template_id, script_text, voice, status, progress,
            main_video_asset_id, background_asset_id, product_asset_id, bgm_asset_id,
            subtitle_style_json)
           VALUES (?, ?, ?, ?, 'pending', 0, ?, ?, ?, ?, ?)""",
        (f"视频_{int(time.time())}", template_id, script, voice,
         mv_id, bg_id, prod_id, bgm_id,
         json.dumps(subtitle_style, ensure_ascii=False))
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()

    background_tasks.add_task(
        run_pipeline_bg,
        project_id, script, voice, template_id,
        mv_id, bg_id, prod_id, bgm_id,
        mv_scale, prod_scale, prod_pos, bvol,
        sub_fs, sub_pos, sub_st,
        mv_x, mv_y, out_w, out_h,
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
        raise HTTPException(status_code=404, detail="项目不存在")
    return dict(row)


@router.post("/render/test")
async def render_test():
    """V1.3 smoke test with synthetic assets."""
    from app.services.ffmpeg_service import generate_test_assets, render_video_v12, detect_media

    output_dir = BASE_DIR / "outputs"
    os.makedirs(output_dir, exist_ok=True)
    start = time.time()
    assets = generate_test_assets(str(output_dir))
    if not assets.get("main_video") or not assets.get("audio"):
        raise HTTPException(status_code=500, detail="Test asset generation failed")
    info = detect_media(assets["audio"])
    dur = info.get("duration", 10.0)
    output_path, video_duration = render_video_v12(
        tts_audio_path=assets["audio"],
        target_duration=dur,
        main_video_path=assets["main_video"],
        background_path=assets.get("background"),
        subtitle_path=None,
        output_width=1080, output_height=1920, timeout=180,
    )
    elapsed = time.time() - start
    size_kb = os.path.getsize(output_path) / 1024
    return {
        "success": True, "test_video": output_path,
        "duration": video_duration, "elapsed_seconds": round(elapsed, 1),
        "size_kb": round(size_kb, 0), "status": "PASS" if elapsed < 60 else "SLOW",
    }