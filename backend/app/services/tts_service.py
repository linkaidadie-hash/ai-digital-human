"""
TTS Service using Edge-TTS.
"""
import asyncio
import os
import time
from pathlib import Path
from edge_tts import Communicate

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _get_ffprobe_duration(output_path: str, text: str) -> float:
    """Get audio duration via ffprobe, with fallback estimation."""
    import subprocess
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        output_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    # Fallback: ~150 chars per minute for Chinese
    return len(text) / 2.5


async def generate_tts_async(text: str, voice: str, output_path: str) -> float:
    """
    Generate TTS audio using Edge-TTS.
    Returns the duration of the generated audio in seconds.
    """
    communicate = Communicate(text, voice)
    await communicate.save(output_path)
    return _get_ffprobe_duration(output_path, text)


def _generate_tts_sync(text: str, voice: str, output_path: str) -> float:
    """
    Synchronous TTS generation — runs the async coroutine in a new event loop.
    """
    try:
        loop = asyncio.get_running_loop()
        # Already in async context — create a future and run in new loop
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            f = pool.submit(asyncio.run, generate_tts_async(text, voice, output_path))
            return f.result(timeout=120)
    except RuntimeError:
        # No running loop — use asyncio.run directly
        return asyncio.run(generate_tts_async(text, voice, output_path))


def generate_tts(text: str, voice: str = "zh-CN-XiaoxiaoNeural",
                 output_dir: str = None) -> tuple[str, float]:
    """
    Generate TTS audio via Edge-TTS.
    Returns: (output_path, duration)
    """
    if output_dir is None:
        output_dir = BASE_DIR / "outputs"

    os.makedirs(output_dir, exist_ok=True)

    output_filename = f"tts_{int(time.time() * 1000)}.mp3"
    output_path = os.path.join(output_dir, output_filename)

    duration = _generate_tts_sync(text, voice, output_path)

    return output_path, duration