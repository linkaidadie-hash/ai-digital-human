"""
Pipeline Router V1.3 - Unified video generation pipeline.
Loads full config from template + script + layout parameters.
"""
import os
import time
import json
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

from app.database import get_db_connection

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineRequest(BaseModel):
    script: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    template_id: Optional[int] = None
    main_video_asset_id: Optional[int] = None
    background_asset_id: Optional[int] = None
    product_asset_id: Optional[int] = None
    bgm_asset_id: Optional[int] = None
    character_image_asset_id: Optional[int] = None
    main_video_scale: float = 0.4
    product_scale: float = 0.25
    product_position: str = "bottom-right"
    bgm_volume: float = 0.15
    subtitle_font_size: int = 48
    subtitle_position: str = "bottom"
    subtitle_stroke: int = 2
    main_video_x: int = 30
    main_video_y: int = 10
    output_width: int = 1080
    output_height: int = 1920

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def update_project(project_id: int, **kwargs):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for key, value in kwargs.items():
            val_str = "NULL" if value is None else str(value)
            cursor.execute(f"UPDATE projects SET {key} = ? WHERE id = ?", (val_str, project_id))
        conn.commit()
        # Verify the update worked
        cursor.execute("SELECT id, status, progress, output_path FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            print(f"[Pipeline] update_project({project_id}): row not found!")
        else:
            if kwargs.get("status"):
                print(f"[Pipeline] DB update: id={project_id} status={row['status']} progress={row['progress']}")
    except Exception as e:
        print(f"[Pipeline] update_project error: {e}")
        import traceback; traceback.print_exc()


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
    character_image_asset_id: int,
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
        character_image_path = _get_asset_path(character_image_asset_id)

        log(f"[Pipeline] Assets — main={main_video_path}, bg={background_path}, "
            f"product={product_path}, bgm={bgm_path}, char_img={character_image_path}")

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
            character_image_path=character_image_path,
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


async def _run_pipeline_bg_async(*args):
    """Async wrapper — runs the sync pipeline function in a thread pool."""
    import asyncio, concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        f = pool.submit(run_pipeline_bg, *args)
        try:
            f.result(timeout=600)
        except Exception as e:
            print(f"[Pipeline] background task error: {e}")


@router.post("/run")
async def run_pipeline(
    body: PipelineRequest,
):
    """Run full pipeline. Loads template defaults, then applies overrides."""
    if not body.script or not body.script.strip():
        raise HTTPException(status_code=400, detail="文案不能为空")

    # Load template to fill in missing params
    tmpl = {}
    if body.template_id:
        tmpl = _get_template(body.template_id)

    mv_id = body.main_video_asset_id if body.main_video_asset_id else tmpl.get("main_video_asset_id")
    bg_id = body.background_asset_id if body.background_asset_id else tmpl.get("background_asset_id")
    prod_id = body.product_asset_id if body.product_asset_id else tmpl.get("product_asset_id")
    bgm_id = body.bgm_asset_id if body.bgm_asset_id else tmpl.get("bgm_asset_id")
    char_img_id = body.character_image_asset_id if body.character_image_asset_id else tmpl.get("character_image_asset_id")

    # Layout
    layout = tmpl.get("layout_json") or {}
    subtitle_style = tmpl.get("subtitle_style_json") or {}

    # Scale & position
    mv_scale = body.main_video_scale if body.main_video_scale != 0.4 else tmpl.get("main_video_scale", 0.4)
    prod_scale = body.product_scale if body.product_scale != 0.25 else tmpl.get("product_scale", 0.25)
    prod_pos = body.product_position if body.product_position != "bottom-right" else tmpl.get("product_position", "bottom-right")
    bvol = body.bgm_volume if body.bgm_volume != 0.15 else tmpl.get("bgm_volume", 0.15)

    sub_fs = body.subtitle_font_size if body.subtitle_font_size != 48 else subtitle_style.get("fontSize", 48)
    sub_pos = body.subtitle_position if body.subtitle_position != "bottom" else subtitle_style.get("position", "bottom")
    sub_st = body.subtitle_stroke if body.subtitle_stroke != 2 else subtitle_style.get("stroke", 2)

    mv_x = body.main_video_x if body.main_video_x != 30 else layout.get("mainVideoX", 30)
    mv_y = body.main_video_y if body.main_video_y != 10 else layout.get("mainVideoY", 10)

    out_w = body.output_width or tmpl.get("output_width", 1080)
    out_h = body.output_height or tmpl.get("output_height", 1920)

# Create project with status=pending
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO projects
               (name, template_id, script_text, voice, status, progress,
                main_video_asset_id, background_asset_id, product_asset_id, bgm_asset_id,
                subtitle_style_json)
               VALUES (?, ?, ?, ?, 'pending', 0, ?, ?, ?, ?, ?)""",
            (f"视频_{int(time.time())}", body.template_id, body.script, body.voice,
             mv_id, bg_id, prod_id, bgm_id,
             json.dumps(subtitle_style, ensure_ascii=False))
        )
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except Exception as dbg:
        import traceback
        print("[DEBUG] DB error: " + traceback.format_exc())
        raise

    # Build worker args and spawn
    worker_script = os.path.join(BASE_DIR, "render_worker.py")
    args = [
        "py", "-u", worker_script,
        str(project_id),
        body.script,
        body.voice,
        str(mv_id if mv_id else 0),
        str(bg_id if bg_id else 0),
        str(prod_id if prod_id else 0),
        str(bgm_id if bgm_id else "None"),
        str(char_img_id if char_img_id else "None"),
        str(mv_scale),
        str(prod_scale),
        prod_pos,
        str(bvol),
        str(sub_fs),
        sub_pos,
        str(sub_st),
        str(mv_x),
        str(mv_y),
        str(out_w),
        str(out_h),
    ]
    subprocess.Popen(args, cwd=BASE_DIR)

    return {
        "success": True,
        "project_id": project_id,
        "status": "pending",
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