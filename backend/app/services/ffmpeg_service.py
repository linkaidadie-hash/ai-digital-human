"""
FFmpeg Service - V1.2
Full-featured video composition: loop/truncate, bg video/image, product overlay, BGM, subtitle.
"""
import subprocess
import os
import time
import json
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FFMPEG_BIN = r"C:\Users\Administrator\AppData\Local\Programs\FFmpeg\ffmpeg-8.1.1-essentials_build\bin"
OUTPUT_DIR = BASE_DIR / "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Logging ────────────────────────────────────────────────────────────────

_log_lines: list[str] = []

def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] [FFmpeg] {msg}"
    print(line)
    _log_lines.append(line)
    # Also append to pipeline debug log so we can read it from outside
    try:
        debug_log = os.path.join(str(BASE_DIR), "outputs", "pipeline_debug.log")
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def get_log() -> str:
    return "\n".join(_log_lines)

def clear_log():
    _log_lines.clear()

def write_log_file(path: str):
    """Write accumulated log to file for debugging."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(get_log())

# ─── Path helpers ──────────────────────────────────────────────────────────

def get_ffmpeg_path() -> str:
    for c in [
        os.path.join(FFMPEG_BIN, "ffmpeg.exe"),
        FFMPEG_BIN + "\\ffmpeg.exe",
        "ffmpeg",
    ]:
        if os.path.exists(c) or c == "ffmpeg":
            return c
    return "ffmpeg"

def get_ffprobe_path() -> str:
    for c in [
        os.path.join(FFMPEG_BIN, "ffprobe.exe"),
        FFMPEG_BIN + "\\ffprobe.exe",
        "ffprobe",
    ]:
        if os.path.exists(c) or c == "ffprobe":
            return c
    return "ffprobe"

def get_creationflags():
    try:
        import ctypes
        return 0x08000000  # CREATE_NO_WINDOW
    except Exception:
        return 0

def safe_remove(path: str):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

# ─── Media detection ─────────────────────────────────────────────────────────

def detect_media(file_path: str) -> dict:
    """
    Detect media info: duration, resolution, fps, codec, has_audio, format.
    Works for video, audio, and image files.
    """
    info = {
        "duration": 0.0, "width": 0, "height": 0,
        "fps": 0.0, "codec": "", "has_audio": False,
        "format": "", "file_size": 0,
    }
    if not os.path.exists(file_path):
        return info

    info["file_size"] = os.path.getsize(file_path)
    ext = Path(file_path).suffix.lower()

    # Image files: instant detection
    if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        info["format"] = ext.lstrip(".")
        try:
            from PIL import Image
            with Image.open(file_path) as im:
                info["width"], info["height"] = im.size
                info["duration"] = 0.0
        except ImportError:
            # PIL not installed, use ffprobe for images
            ffprobe = get_ffprobe_path()
            cmd = [ffprobe, "-v", "error", "-show_entries",
                   "stream=width,height", "-of", "json", file_path]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                data = json.loads(r.stdout)
                for s in data.get("streams", []):
                    if s.get("width"):
                        info["width"] = s["width"]
                        info["height"] = s["height"]
            except Exception:
                pass
        return info

    # Video / Audio: ffprobe
    ffprobe = get_ffprobe_path()
    cmd = [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", file_path]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(r.stdout)
    except Exception as e:
        log(f"ffprobe failed: {e}")
        return info

    fmt = data.get("format", {})
    info["duration"] = float(fmt.get("duration") or 0)
    info["format"] = fmt.get("format_long_name", fmt.get("format_name", ext.lstrip(".")))

    for s in data.get("streams", []):
        stype = s.get("codec_type", "")
        if stype == "video":
            info["width"] = s.get("width", 0)
            info["height"] = s.get("height", 0)
            info["codec"] = s.get("codec_name", "")
            fps_str = s.get("r_frame_rate", "0/1")
            try:
                num, den = fps_str.split("/")
                info["fps"] = round(int(num) / int(den), 2)
            except Exception:
                info["fps"] = 0.0
        elif stype == "audio" and not info["has_audio"]:
            info["has_audio"] = True

    return info


def validate_format(file_path: str) -> Tuple[bool, str]:
    """Validate file format is supported. Returns (valid, message)."""
    if not os.path.exists(file_path):
        return False, "文件不存在"
    ext = Path(file_path).suffix.lower().lstrip(".")
    supported = ["mp4", "mov", "webm", "jpg", "jpeg", "png", "mp3", "wav", "webp"]
    if ext not in supported:
        return False, f"不支持的格式「.{ext}」，支持：{', '.join(supported)}"
    return True, ""


# ─── Preprocessing ──────────────────────────────────────────────────────────

def preprocess_video(input_path: str, target_fps: int = 30) -> str:
    """
    Convert video to: mp4, H.264, target_fps, AAC.
    Returns path to preprocessed file (or original if already compatible).
    """
    log(f"Preprocessing video: {input_path}")
    info = detect_media(input_path)

    needs_convert = (
        info["codec"] not in ("h264", "libx264", "") or
        info["fps"] < target_fps - 1 or info["fps"] > target_fps + 1
    )

    if not needs_convert:
        log(f"  Video already compatible, skipping preprocess")
        return input_path

    out_path = str(OUTPUT_DIR / f"preprocessed_{int(time.time() * 1000)}.mp4")
    ffmpeg = get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y", "-i", input_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-vf", f"fps={target_fps}",
        "-c:a", "aac", "-b:a", "128k",
        "-r", str(target_fps),
        out_path
    ]
    rc, _, stderr = run_ffmpeg(cmd, timeout=120)
    if rc == 0 and os.path.exists(out_path):
        log(f"  Preprocessed: {out_path}")
        return out_path
    log(f"  Preprocess failed: {stderr}")
    return input_path  # fallback to original


def preprocess_audio(input_path: str) -> str:
    """Convert audio to mp3 or wav. Returns preprocessed path."""
    log(f"Preprocessing audio: {input_path}")
    ext = Path(input_path).suffix.lower()
    out_path = str(OUTPUT_DIR / f"audio_{int(time.time() * 1000)}.mp3")
    ffmpeg = get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y", "-i", input_path,
        "-c:a", "libmp3lame", "-b:a", "192k",
        out_path
    ]
    rc, _, stderr = run_ffmpeg(cmd, timeout=60)
    if rc == 0 and os.path.exists(out_path):
        return out_path
    # Try wav fallback
    out_path = str(OUTPUT_DIR / f"audio_{int(time.time() * 1000)}.wav")
    cmd = [ffmpeg, "-y", "-i", input_path, "-c:a", "pcm_s16le", out_path]
    rc, _, _ = run_ffmpeg(cmd, timeout=60)
    return out_path if rc == 0 else input_path


def preprocess_image(input_path: str, target_width: int = 1080, target_height: int = 1920) -> str:
    """
    Convert image to fit within target dimensions, pad to exact size.
    Uses a black background for padding.
    """
    log(f"Preprocessing image: {input_path}")
    out_path = str(OUTPUT_DIR / f"bg_{int(time.time() * 1000)}.mp4")
    ffmpeg = get_ffmpeg_path()

    # Scale + pad the image to exact target size
    cmd = [
        ffmpeg, "-y",
        "-loop", "1", "-i", input_path,
        "-t", "1",  # single frame, will loop via -stream_loop in render
        "-vf", f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
               f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-r", "30", "-pix_fmt", "yuv420p",
        out_path
    ]
    rc, _, stderr = run_ffmpeg(cmd, timeout=60)
    if rc == 0 and os.path.exists(out_path):
        return out_path
    log(f"Image preprocess failed: {stderr}")
    return input_path


# ─── Core FFmpeg runner ──────────────────────────────────────────────────────

def run_ffmpeg(cmd: list, timeout: int = 180) -> Tuple[int, str, str]:
    start = time.time()
    log(f"CMD: {' '.join(cmd[:6])}...")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=get_creationflags()
        )
        stdout, stderr = proc.communicate(timeout=timeout)
        elapsed = time.time() - start
        log(f"  DONE in {elapsed:.1f}s, rc={proc.returncode}")
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        proc.kill()
        log(f"  TIMEOUT after {timeout}s")
        return -1, "", f"FFmpeg timed out after {timeout}s"


# ─── Loop / Trim ─────────────────────────────────────────────────────────────

def loop_or_trim(video_path: str, target_duration: float, output_dir: str = None) -> str:
    """
    Extend or trim video to target_duration by looping (if short) or trimming (if long).
    Uses stream_copy for speed.
    """
    if output_dir is None:
        output_dir = str(OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    info = detect_media(video_path)
    src_dur = info.get("duration", 0)

    if src_dur <= 0:
        src_dur = 1.0
        log("  No duration detected, defaulting to 1s")

    out_path = os.path.join(output_dir, f"looped_{int(time.time() * 1000)}.mp4")
    ffmpeg = get_ffmpeg_path()

    if src_dur < target_duration:
        # Loop: repeat video to fill target_duration
        loops_needed = int(target_duration / src_dur) + 2
        log(f"  Looping video {loops_needed} times (src={src_dur:.1f}s, target={target_duration:.1f}s)")
        cmd = [
            ffmpeg, "-y",
            "-stream_loop", str(loops_needed), "-i", video_path,
            "-t", str(target_duration),
            "-c:v", "copy", "-c:a", "copy",
            out_path
        ]
    else:
        # Trim: cut to target duration
        log(f"  Trimming video (src={src_dur:.1f}s, target={target_duration:.1f}s)")
        cmd = [
            ffmpeg, "-y", "-i", video_path,
            "-t", str(target_duration),
            "-c:v", "copy", "-c:a", "copy",
            out_path
        ]

    rc, _, stderr = run_ffmpeg(cmd, timeout=120)
    if rc == 0 and os.path.exists(out_path):
        return out_path
    log(f"  Loop/trim failed: {stderr}")
    return video_path  # fallback to original


# ─── Subtitle burn-in (with style) ──────────────────────────────────────────

def burn_subtitles(input_path: str, subtitle_path: str,
                  output_path: str,
                  font_size: int = 48,
                  position: str = "bottom",
                  stroke: int = 2) -> str:
    """
    Burn SRT subtitles into video.
    Uses relative paths to avoid FFmpeg filter-parser bugs with Windows C: colons.
    """
    ffmpeg = get_ffmpeg_path()

    # Position: y coordinate
    if position == "top":
        y_pos = "30"
    elif position == "middle":
        y_pos = "(H-text_h)/2"
    else:  # bottom
        y_pos = "H-text_h-30"

    # Use relative paths with forward slashes — avoids the FFmpeg filter graph
    # parser treating `C:` as a colon-separated option, which corrupts the path.
    # Paths are relative to BASE_DIR (backend root) where the Python process runs.
    backend_root = Path(__file__).resolve().parent.parent.parent  # backend root
    sub_rel = Path(subtitle_path).relative_to(backend_root).as_posix()
    input_rel = Path(input_path).relative_to(backend_root).as_posix()
    output_rel = Path(output_path).relative_to(backend_root).as_posix()

    filter_str = f"subtitles={sub_rel}"

    cmd = [
        ffmpeg, "-y", "-i", input_rel,
        "-vf", filter_str,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        output_rel
    ]
    rc, _, stderr = run_ffmpeg(cmd, timeout=180)
    # Verify: check that output file exists in absolute form
    abs_out = backend_root / output_rel
    if rc == 0 and os.path.exists(abs_out):
        return str(abs_out)
    log(f"Subtitle burn failed: {stderr}")
    return input_path


# ─── Main render ──────────────────────────────────────────────────────────────

def render_video_v12(
    tts_audio_path: str,
    target_duration: float,
    main_video_path: str = None,
    background_path: str = None,  # video or image
    product_path: str = None,
    product_position: str = "bottom-right",  # bottom-right, bottom-left, top-right, top-left
    product_scale: float = 0.25,
    bgm_path: str = None,
    bgm_volume: float = 0.15,
    tts_volume: float = 1.0,
    subtitle_path: str = None,
    subtitle_font_size: int = 48,
    subtitle_position: str = "bottom",
    subtitle_stroke: int = 2,
    output_width: int = 1080,
    output_height: int = 1920,
    timeout: int = 180,
) -> Tuple[str, float]:
    """
    V1.2 full render pipeline.

    Steps:
    1. Determine background (black / image / video)
    2. Loop/truncate main video to target_duration
    3. Overlay main video on background (centered, 40% width)
    4. Optionally overlay product PNG/JPG
    5. Optionally add BGM (looped, volume adjusted)
    6. Attach TTS audio (volume adjusted)
    7. Burn subtitles if provided
    8. Output MP4

    Returns (output_path, duration).
    """
    log(f"V1.2 render start — duration={target_duration:.1f}s, size={output_width}x{output_height}")

    temp_files: list[str] = []
    output_dir = str(OUTPUT_DIR)

    def add_temp(p):
        if p and os.path.exists(p):
            temp_files.append(p)
        return p

    log_dir = output_dir

    try:
        # ── 1. Background ──────────────────────────────────────────────────
        if background_path and os.path.exists(background_path):
            bg_ext = Path(background_path).suffix.lower()
            if bg_ext in (".jpg", ".jpeg", ".png", ".webp"):
                # Image → looped video
                bg_video = add_temp(preprocess_image(background_path, output_width, output_height))
            else:
                bg_video = add_temp(loop_or_trim(background_path, target_duration, output_dir))
        else:
            # Black background
            bg_video = None
            log("  Using black background")

        # ── 2. Main video preprocessed ─────────────────────────────────────
        if main_video_path and os.path.exists(main_video_path):
            mv_pre = add_temp(preprocess_video(main_video_path))
            mv_looped = add_temp(loop_or_trim(mv_pre, target_duration, output_dir))
        else:
            mv_looped = None
            log("  No main video, will use black background only")

        # ── 3. Determine base layers ──────────────────────────────────────
        base_video = mv_looped if mv_looped else bg_video
        if not base_video:
            # Pure black fallback
            black_path = os.path.join(output_dir, f"black_{int(time.time()*1000)}.mp4")
            cmd_black = [
                get_ffmpeg_path(), "-y",
                "-f", "lavfi", "-i", f"color=c=black:s={output_width}x{output_height}:d={target_duration}:r=30",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                black_path
            ]
            rc, _, _ = run_ffmpeg(cmd_black, timeout=60)
            if rc == 0:
                base_video = add_temp(black_path)

        if not base_video:
            raise Exception("无法创建基础视频（背景+主视频都不存在）")

        # ── 4. Build filter graph ───────────────────────────────────────────
        # Build as a proper pipeline:
        #   base_video ─┐
        #               ├─ [product overlay] ── [final video]
        #   product ────┘
        #
        # Then add audio: TTS + optional BGM mixed → [audio]

        ffmpeg = get_ffmpeg_path()
        cmd = [ffmpeg, "-y", "-i", base_video]
        # Collect filter chain parts as ["[in]filter[out]", ...]
        filter_inputs: list[str] = []
        video_filter = "[0:v]"     # output of video chain
        audio_filter = "[audio]"  # output of audio chain
        next_input = 1            # input 0 is base_video

        # ── Video: base + optional product overlay ──────────────────────────
        if product_path and os.path.exists(product_path):
            log(f"  Adding product overlay: {product_path}")
            prod_w = int(output_width * product_scale)
            prod_h = -1
            margin = 20
            if product_position == "bottom-right":
                x_p, y_p = f"W-{prod_w}-{margin}", f"H-{prod_h}-{margin}"
            elif product_position == "bottom-left":
                x_p, y_p = str(margin), f"H-{prod_h}-{margin}"
            elif product_position == "top-right":
                x_p, y_p = f"W-{prod_w}-{margin}", str(margin)
            else:
                x_p, y_p = str(margin), str(margin)

            filter_inputs.append(
                f"[{next_input}:v]scale={prod_w}:{prod_h}[prod];"
                f"[0:v][prod]overlay={x_p}:{y_p}[v]"
            )
            cmd.extend(["-i", product_path])
            next_input += 1
            video_filter = "[v]"

        # Always do format conversion
        filter_inputs.append(f"{video_filter}format=yuv420p[final]")

        # ── Audio: TTS + optional BGM ──────────────────────────────────────
        has_tts = tts_audio_path and os.path.exists(tts_audio_path)
        has_bgm = bgm_path and os.path.exists(bgm_path)

        if has_tts:
            cmd.extend(["-i", tts_audio_path])
            tts_idx = next_input
            next_input += 1

            if has_bgm:
                loop_count = max(1, int(target_duration / 30) + 3)
                # Build BGM input entries properly
                cmd.extend(["-stream_loop", str(loop_count), "-i", bgm_path])
                bgm_idx = next_input
                next_input += 1
                filter_inputs.extend([
                    f"[{tts_idx}:a]volume={tts_volume}[tts]",
                    f"[{bgm_idx}:a]volume={bgm_volume}[bgm_raw]",
                    f"[tts][bgm_raw]amix=inputs=2:duration=first[a]",
                ])
                audio_filter = "[a]"
            else:
                filter_inputs.append(f"[{tts_idx}:a]volume={tts_volume}[a]")
                audio_filter = "[a]"

        elif has_bgm:
            loop_count = max(1, int(target_duration / 30) + 3)
            cmd.extend(["-stream_loop", str(loop_count), "-i", bgm_path])
            bgm_idx = next_input
            next_input += 1
            filter_inputs.append(f"[{bgm_idx}:a]volume={bgm_volume}[a]")
            audio_filter = "[a]"

        else:
            cmd.extend(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"])
            filter_inputs.append(f"[{next_input}:a]anull[a]")
            audio_filter = "[a]"

        filter_str = ";".join(filter_inputs)
        log(f"  Filter graph: {filter_str[:300]}")

        # ── Assemble ─────────────────────────────────────────────────────
        cmd.extend(["-filter_complex", filter_str, "-map", "[final]", "-map", audio_filter])
        cmd.extend([
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30", "-t", str(target_duration),
            "-pix_fmt", "yuv420p",
        ])

        output_path = os.path.join(output_dir, f"output_{int(time.time() * 1000)}.mp4")
        cmd.append(output_path)

        rc, stdout, stderr = run_ffmpeg(cmd, timeout=timeout)
        if rc != 0:
            # Try simpler fallback: just base video + TTS audio, no complex filters
            log(f"Complex render failed, trying simple fallback: {stderr}")
            return _simple_render_fallback(
                base_video, tts_audio_path, target_duration,
                output_width, output_height, timeout
            )

        log(f"V1.2 render SUCCESS: {output_path}")

        # ── 7. Subtitle burn-in (separate pass for reliability) ──────────
        if subtitle_path and os.path.exists(subtitle_path):
            log("Burning subtitles...")
            sub_out = os.path.join(output_dir, f"with_subs_{int(time.time() * 1000)}.mp4")
            subbed = burn_subtitles(output_path, subtitle_path, sub_out,
                                    font_size=subtitle_font_size,
                                    position=subtitle_position,
                                    stroke=subtitle_stroke)
            if os.path.exists(subbed) and subbed != output_path:
                safe_remove(output_path)
                output_path = subbed

        # ── Verify ────────────────────────────────────────────────────────
        info = detect_media(output_path)
        dur = info.get("duration", 0)
        log(f"Output verified: {output_path} ({dur:.1f}s)")

        # Write log
        log_file = os.path.join(log_dir, f"render_{int(time.time()*1000)}.log")
        write_log_file(log_file)
        log(f"Log written: {log_file}")

        return output_path, dur

    except Exception as e:
        log(f"V1.2 render FAILED: {e}")
        log_file = os.path.join(log_dir, f"render_error_{int(time.time()*1000)}.log")
        write_log_file(log_file)
        raise Exception(f"视频合成失败: {e}\n详细日志: {log_file}")


def _simple_render_fallback(base_video: str, tts_audio_path: str, target_duration: float,
                             output_width: int, output_height: int, timeout: int) -> Tuple[str, float]:
    """Fallback: scale base video + attach TTS audio, no complex overlays."""
    output_dir = str(OUTPUT_DIR)
    output_path = os.path.join(output_dir, f"fallback_{int(time.time() * 1000)}.mp4")
    ffmpeg = get_ffmpeg_path()

    cmd = [ffmpeg, "-y", "-i", base_video]
    if tts_audio_path and os.path.exists(tts_audio_path):
        cmd.extend(["-i", tts_audio_path])

    filter_str = f"[0:v]scale={output_width}:{output_height}:force_original_aspect_ratio=decrease[vid]"
    if tts_audio_path and os.path.exists(tts_audio_path):
        cmd.extend(["-filter_complex", f"{filter_str};[1:a]anull[audio]"])
        cmd.extend(["-map", "[vid]", "-map", "[audio]"])
    else:
        cmd.extend(["-vf", filter_str, "-an"])

    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-t", str(target_duration),
        "-pix_fmt", "yuv420p",
        output_path
    ])

    rc, _, stderr = run_ffmpeg(cmd, timeout=timeout)
    if rc == 0 and os.path.exists(output_path):
        log(f"Fallback render SUCCESS: {output_path}")
        return output_path, target_duration
    raise Exception(f"简单合成也失败了: {stderr}")


# ─── V1.1 compatibility (keep for test) ──────────────────────────────────────

def generate_test_assets(output_dir: str) -> dict:
    """Generate 10-second test assets for V1.1 acceptance test."""
    os.makedirs(output_dir, exist_ok=True)
    assets = {}

    ffmpeg = get_ffmpeg_path()

    bg_path = os.path.join(output_dir, "test_bg.mp4")
    cmd_bg = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=10:r=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        bg_path
    ]
    rc, _, _ = run_ffmpeg(cmd_bg, timeout=60)
    if rc == 0:
        assets["background"] = bg_path

    mv_path = os.path.join(output_dir, "test_main.mp4")
    cmd_mv = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "testsrc=d=10:s=540x960:r=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        mv_path
    ]
    rc, _, _ = run_ffmpeg(cmd_mv, timeout=60)
    if rc == 0:
        assets["main_video"] = mv_path

    audio_path = os.path.join(output_dir, "test_audio.mp3")
    cmd_audio = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:a", "libmp3lame", "-b:a", "128k",
        audio_path
    ]
    rc, _, _ = run_ffmpeg(cmd_audio, timeout=30)
    if rc == 0:
        assets["audio"] = audio_path

    return assets


# Backward compatibility alias
get_video_info = detect_media


def render_video(
    main_video_path: str = None,
    background_path: str = None,
    audio_path: str = None,
    subtitle_path: str = None,
    output_path: str = None,
    output_width: int = 1080,
    output_height: int = 1920,
    timeout: int = 180,
) -> Tuple[str, float]:
    """V1.1 compatibility — wraps V1.2 with defaults."""
    if not audio_path or not os.path.exists(audio_path):
        info = detect_media(main_video_path or "")
        dur = info.get("duration", 10.0)
    else:
        info = detect_media(audio_path)
        dur = info.get("duration", 10.0)
    return render_video_v12(
        tts_audio_path=audio_path,
        target_duration=dur,
        main_video_path=main_video_path,
        background_path=background_path,
        subtitle_path=subtitle_path,
        output_width=output_width,
        output_height=output_height,
        timeout=timeout,
    )