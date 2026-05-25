"""
FFmpeg Service - Video composition.
"""
import subprocess
import os
import time
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_ffmpeg_path() -> str:
    """Get ffmpeg path from settings or system PATH."""
    from app.database import get_setting
    ffmpeg_path = get_setting("ffmpeg_path", "ffmpeg")
    # Fallback: use known FFmpeg installation path
    if ffmpeg_path == "ffmpeg" or not ffmpeg_path:
        ffmpeg_default = r"C:\Users\Administrator\AppData\Local\Programs\FFmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
        import os as _os
        if _os.path.exists(ffmpeg_default):
            ffmpeg_path = ffmpeg_default
    return ffmpeg_path


def get_video_info(file_path: str) -> dict:
    """
    Get video information using ffprobe.
    Returns: {duration, width, height}
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json",
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        import json
        info = json.loads(result.stdout)
        stream = info.get("streams", [{}])[0]
        return {
            "duration": float(stream.get("duration", 0)),
            "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0))
        }
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {"duration": 0, "width": 0, "height": 0}


def render_video(
    main_video_path: Optional[str] = None,
    background_path: Optional[str] = None,
    audio_path: Optional[str] = None,
    subtitle_path: Optional[str] = None,
    bgm_path: Optional[str] = None,
    output_path: Optional[str] = None,
    output_width: int = 1080,
    output_height: int = 1920,
    layout_json: Optional[str] = None
) -> tuple[str, float]:
    """
    Render final video with FFmpeg.
    - Background: stretched to fill
    - Main video: overlaid based on layout_json
    - Audio: TTS audio + BGM (15-25% volume)
    - Subtitles: burned into video

    Args:
        main_video_path: Path to main character video
        background_path: Path to background image/video
        audio_path: Path to TTS audio
        subtitle_path: Path to SRT subtitle file
        bgm_path: Path to background music
        output_path: Output video path
        output_width: Output width
        output_height: Output height
        layout_json: JSON string with layout info

    Returns:
        (output_path, duration)
    """
    import json

    ffmpeg = get_ffmpeg_path()

    if output_path is None:
        output_dir = BASE_DIR / "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"output_{int(time.time() * 1000)}.mp4")

    # Parse layout
    layout = {}
    if layout_json:
        try:
            layout = json.loads(layout_json)
        except json.JSONDecodeError:
            pass

    # Default character position (center, 40% width, 80% height)
    char_layout = layout.get("character", {"x": 0.5, "y": 0.5, "w": 0.4, "h": 0.8})
    product_layout = layout.get("product", {"x": 0.8, "y": 0.7, "w": 0.15, "h": 0.2})

    # Build FFmpeg command
    filters = []
    inputs = []
    filter_complex = ""
    audio_inputs = []

    input_idx = 0

    # Background layer (base)
    if background_path and os.path.exists(background_path):
        inputs.append(f"-i \"{background_path}\"")
        bg_idx = input_idx
        input_idx += 1

        # Check if it's a video or image
        if background_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            # Video background
            filters.append(f"[{bg_idx}:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,crop={output_width}:{output_height}[bg]")
        else:
            # Image background - stretch to fill
            filters.append(f"[{bg_idx}:v]scale={output_width}:{output_height}:force_original_aspect_ratio=increase,crop={output_width}:{output_height}[bg]")
    else:
        # No background - create black canvas
        filters.append(f"color=c=black:s={output_width}x{output_height}[bg]")

    # Main video layer
    if main_video_path and os.path.exists(main_video_path):
        inputs.append(f"-i \"{main_video_path}\"")
        main_idx = input_idx
        input_idx += 1

        # Scale and position main video
        x_pos = int(char_layout["x"] * output_width - (char_layout["w"] * output_width) / 2)
        y_pos = int(char_layout["y"] * output_height - (char_layout["h"] * output_height) / 2)
        w = int(char_layout["w"] * output_width)
        h = int(char_layout["h"] * output_height)

        filters.append(f"[{main_idx}:v]scale={w}:{h}[main_scaled]")
        filters.append(f"[bg][main_scaled]overlay={x_pos}:{y_pos}[out_base]")
    else:
        filters.append(f"[bg]copy[out_base]")

    # Product overlay
    if product_layout and os.path.exists(product_layout.get("asset_path", "")):
        pass  # Product overlay can be added similarly

    # Build filter complex string
    if len(filters) > 1:
        filter_complex = "-filter_complex \"" + ";".join(filters) + "\""
    else:
        filter_complex = ""

    # Build base command
    if inputs:
        cmd = f'"{ffmpeg}" -y '
        cmd += " ".join(inputs)

        # Video filter
        if filter_complex:
            cmd += f" {filter_complex}"

        # Map video
        if "out_base" in filter_complex:
            cmd += " -map \"[out_base]\""
        elif inputs:
            cmd += f" -map {0}:v"

        # Map audio (TTS) — audio input index is tracked separately
        audio_idx_for_map = input_idx
        if audio_path and os.path.exists(audio_path):
            inputs.append(f"-i \"{audio_path}\"")
            audio_idx_for_map = input_idx
            cmd += f" -map {audio_idx_for_map}:a"
            input_idx += 1

        # Add BGM with volume adjustment
        bgm_idx_for_map = input_idx
        if bgm_path and os.path.exists(bgm_path):
            inputs.append(f"-i \"{bgm_path}\"")
            bgm_idx_for_map = input_idx
            cmd += f" -map {bgm_idx_for_map}:a"
            cmd += " -filter:a \"volume=0.2\""  # 20% volume for BGM
            input_idx += 1

        # If no audio, add silent audio
        if not audio_path and not bgm_path:
            cmd += " -f lavfi -i anullsrc=r=44100:cl=stereo"

        cmd += f' -c:v libx264 -preset medium -crf 23'
        cmd += f' -c:a aac -b:a 128k'
        cmd += f' -r 30'  # 30fps
        cmd += f' -s {output_width}x{output_height}'
        cmd += f' "{output_path}"'

        # Remove extra quotes for system call
        cmd = cmd.replace('"', '')

        print(f"[FFmpeg] Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[FFmpeg] Error: {result.stderr}")
            raise Exception(f"FFmpeg failed: {result.stderr}")
    else:
        raise Exception("No input sources provided")

    # Get output duration
    info = get_video_info(output_path)

    return output_path, info.get("duration", 0)