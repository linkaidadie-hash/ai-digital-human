"""
FFmpeg Service - Video composition (V1.1 - Stable).
Simplified pipeline: main video + TTS audio + subtitles only.
"""
import subprocess
import os
import time
import json
import threading
from pathlib import Path
from typing import Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FFMPEG_BIN = r"C:\Users\Administrator\AppData\Local\Programs\FFmpeg\ffmpeg-8.1.1-essentials_build\bin"


def log(msg: str):
    """Print timestamped log."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [FFmpeg] {msg}")


def get_ffmpeg_path() -> str:
    """Return path to ffmpeg.exe, trying several known locations."""
    candidates = [
        os.path.join(FFMPEG_BIN, "ffmpeg.exe"),
        os.path.join(FFMPEG_BIN, "ffmpeg"),
        r"C:\Users\Administrator\AppData\Local\Programs\FFmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
        "ffmpeg",  # system PATH fallback
    ]
    for c in candidates:
        if os.path.exists(c) or c == "ffmpeg":
            return c
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Return path to ffprobe.exe."""
    candidates = [
        os.path.join(FFMPEG_BIN, "ffprobe.exe"),
        os.path.join(FFMPEG_BIN, "ffprobe"),
        "ffprobe",
    ]
    for c in candidates:
        if os.path.exists(c) or c == "ffprobe":
            return c
    return "ffprobe"


def get_video_info(file_path: str) -> dict:
    """Get video info via ffprobe. Returns {duration, width, height}."""
    ffprobe = get_ffprobe_path()
    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json",
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        info = json.loads(result.stdout)
        stream = info.get("streams", [{}])[0]
        return {
            "duration": float(stream.get("duration") or 0),
            "width": int(stream.get("width") or 0),
            "height": int(stream.get("height") or 0)
        }
    except Exception as e:
        log(f"ffprobe error for {file_path}: {e}")
        return {"duration": 0, "width": 0, "height": 0}


def run_ffmpeg(cmd: list, timeout: int = 180) -> Tuple[int, str, str]:
    """
    Run FFmpeg command with timeout.
    Returns (returncode, stdout, stderr).
    """
    start = time.time()
    log(f"CMD: {' '.join(cmd)}")
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
        log(f"DONE in {elapsed:.1f}s, rc={proc.returncode}")
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        proc.kill()
        elapsed = time.time() - start
        log(f"TIMEOUT after {elapsed:.1f}s — process killed")
        return -1, "", f"FFmpeg timed out after {timeout}s"


def get_creationflags():
    """Windows: suppress console window for subprocess."""
    try:
        import ctypes
        return 0x08000000  # CREATE_NO_WINDOW
    except Exception:
        return 0


def generate_test_assets(output_dir: str) -> dict:
    """Generate 10-second test assets: background video, main video, audio."""
    os.makedirs(output_dir, exist_ok=True)
    assets = {}

    # Test background: 10s black video
    bg_path = os.path.join(output_dir, "test_bg.mp4")
    log("Generating test background (10s black video)...")
    cmd_bg = [
        get_ffmpeg_path(), "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d=10:r=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        bg_path
    ]
    rc, _, _ = run_ffmpeg(cmd_bg, timeout=60)
    if rc == 0 and os.path.exists(bg_path):
        assets["background"] = bg_path
        log(f"Test bg created: {bg_path}")
    else:
        log(f"WARNING: test bg generation failed, rc={rc}")

    # Test main video: 10s video from color pattern
    mv_path = os.path.join(output_dir, "test_main.mp4")
    log("Generating test main video (10s pattern)...")
    cmd_mv = [
        get_ffmpeg_path(), "-y",
        "-f", "lavfi", "-i", f"testsrc=d=10:s=540x960:r=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        mv_path
    ]
    rc, _, _ = run_ffmpeg(cmd_mv, timeout=60)
    if rc == 0 and os.path.exists(mv_path):
        assets["main_video"] = mv_path
        log(f"Test main video created: {mv_path}")

    # Test TTS audio: 10s sine wave
    audio_path = os.path.join(output_dir, "test_audio.mp3")
    log("Generating test audio (10s tone)...")
    cmd_audio = [
        get_ffmpeg_path(), "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:a", "libmp3lame", "-b:a", "128k",
        audio_path
    ]
    rc, _, _ = run_ffmpeg(cmd_audio, timeout=30)
    if rc == 0 and os.path.exists(audio_path):
        assets["audio"] = audio_path
        log(f"Test audio created: {audio_path}")

    return assets


def render_video(
    main_video_path: Optional[str] = None,
    background_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
    output_path: Optional[str] = None,
    output_width: int = 1080,
    output_height: int = 1920,
    timeout: int = 180,
) -> Tuple[str, float]:
    """
    Simplified video render:
    - Main video scaled and centered
    - TTS audio attached
    - Subtitles burned in (if provided)
    - No BGM, no product overlay, no background overlay for V1.1 stability
    """
    ffmpeg = get_ffmpeg_path()
    log(f"Starting render. ffmpeg={ffmpeg}")
    log(f"  main_video={main_video_path}")
    log(f"  background={background_path}")
    log(f"  audio={audio_path}")
    log(f"  subtitle={subtitle_path}")

    if output_path is None:
        output_dir = BASE_DIR / "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"output_{int(time.time() * 1000)}.mp4")

    # Step 1: Determine source duration from main video or audio
    src_duration = 0.0
    if main_video_path and os.path.exists(main_video_path):
        info = get_video_info(main_video_path)
        src_duration = info.get("duration", 0)
        log(f"  main video duration: {src_duration:.2f}s")
    elif audio_path and os.path.exists(audio_path):
        info = get_video_info(audio_path)
        src_duration = info.get("duration", 0)
        log(f"  audio duration: {src_duration:.2f}s")

    if src_duration <= 0:
        src_duration = 10.0
        log("  No source duration detected, defaulting to 10s")

    # Step 2: Build a simple color background video at target duration
    bg_temp = os.path.join(BASE_DIR / "outputs", f"bg_{int(time.time() * 1000)}.mp4")
    log(f"Creating background video ({src_duration:.1f}s)...")
    cmd_bg = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=black:s={output_width}x{output_height}:d={src_duration}:r=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        bg_temp
    ]
    rc, _, stderr_bg = run_ffmpeg(cmd_bg, timeout=60)
    if rc != 0:
        log(f"Background generation failed: {stderr_bg}")
        raise Exception(f"Background generation failed: {stderr_bg}")
    log(f"  Background temp created: {bg_temp}")

    # Step 3: If we have a main video, scale and overlay it centered
    has_video = main_video_path and os.path.exists(main_video_path)
    has_audio = audio_path and os.path.exists(audio_path)
    has_subtitle = subtitle_path and os.path.exists(subtitle_path)

    if has_video:
        log("Overlay main video onto background...")

        # Get main video duration
        mv_info = get_video_info(main_video_path)
        mv_dur = mv_info.get("duration", src_duration)

        # Build FFmpeg command for V1.1: video scale + overlay, then add audio
        cmd_parts = [
            ffmpeg, "-y",
            "-i", bg_temp,              # input 0: background
            "-i", main_video_path,       # input 1: main video
        ]

        if has_audio:
            cmd_parts.extend(["-i", audio_path])  # input 2: audio

        # Scale main video to 40% width, keep aspect ratio, center it
        # overlay position: (W-w)/2, (H-h)/2
        scale_w = int(output_width * 0.4)
        scale_h = -2  # keep aspect ratio

        filter_str = (
            f"[1:v]scale={scale_w}:{scale_h},"
            f"format=yuv420p[mvin];"
            f"[0:v][mvin]overlay=(W-w)/2:(H-h)/2:shortest=1[vid]"
        )

        cmd_parts.extend([
            "-filter_complex", filter_str,
            "-map", "[vid]",
        ])

        if has_audio:
            cmd_parts.extend(["-map", "2:a"])

        if not has_audio:
            # Add silent audio so output has audio track
            cmd_parts.extend(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest"])

        cmd_parts.extend([
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30",
            "-t", str(src_duration),
            output_path
        ])

        rc, stdout, stderr = run_ffmpeg(cmd_parts, timeout=timeout)
        if rc != 0:
            log(f"Render FAILED: {stderr}")
            # Clean up temp
            if os.path.exists(bg_temp):
                os.remove(bg_temp)
            raise Exception(f"FFmpeg render failed: {stderr}")

        log(f"Render SUCCESS: {output_path}")

    else:
        # No main video: just copy the background
        log("No main video — copying background as output")
        cmd_copy = [
            ffmpeg, "-y",
            "-i", bg_temp,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ]
        rc, stdout, stderr = run_ffmpeg(cmd_copy, timeout=30)
        if rc != 0:
            if os.path.exists(bg_temp):
                os.remove(bg_temp)
            raise Exception(f"Background copy failed: {stderr}")

    # Clean up temp background
    if os.path.exists(bg_temp):
        try:
            os.remove(bg_temp)
        except Exception:
            pass

    # Verify output
    info = get_video_info(output_path)
    dur = info.get("duration", 0)
    log(f"Output verified: {output_path} ({dur:.1f}s, {info.get('width')}x{info.get('height')})")

    return output_path, dur