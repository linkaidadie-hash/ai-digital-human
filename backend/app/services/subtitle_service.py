"""
Subtitle Service - Generate SRT subtitles.
"""
import os
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def generate_subtitles(text: str, duration: float, output_path: str = None) -> tuple[str, int]:
    """
    Generate SRT subtitles by splitting text on punctuation marks.
    Time is distributed evenly across segments.

    Args:
        text: The text to convert to subtitles
        duration: Total duration in seconds
        output_path: Optional output file path

    Returns:
        (output_path, segment_count)
    """
    if output_path is None:
        output_dir = BASE_DIR / "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"subtitle_{int(time.time() * 1000)}.srt")

    # Split by sentence delimiters (Chinese and English punctuation)
    # Keep the delimiters in the segments
    segments = re.split(r'([。！？.!?\n]+)', text)

    # Combine text with its following punctuation
    combined = []
    for i in range(0, len(segments) - 1, 2):
        if i + 1 < len(segments):
            segment_text = segments[i].strip() + segments[i + 1].strip()
        else:
            segment_text = segments[i].strip()
        if segment_text:
            combined.append(segment_text)

    # If no punctuation found, split by character count
    if not combined:
        chars_per_segment = 30
        for i in range(0, len(text), chars_per_segment):
            segment_text = text[i:i + chars_per_segment].strip()
            if segment_text:
                combined.append(segment_text)

    segment_count = len(combined)
    if segment_count == 0:
        combined = [""]  # Empty subtitle
        segment_count = 1

    # Calculate time per segment
    time_per_segment = duration / segment_count

    # Build SRT content
    srt_content = []
    for i, segment_text in enumerate(combined):
        start_time = i * time_per_segment
        end_time = (i + 1) * time_per_segment

        srt_content.append(f"{i + 1}")
        srt_content.append(f"{format_time(start_time)} --> {format_time(end_time)}")
        srt_content.append(segment_text)
        srt_content.append("")  # Empty line between entries

    # Write SRT file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))

    return output_path, segment_count


def format_time(seconds: float) -> str:
    """Format seconds to SRT time format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"