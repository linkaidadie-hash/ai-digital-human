"""
Subtitle Router - Generate SRT subtitles.
"""
from fastapi import APIRouter, HTTPException

from app.models import SubtitleRequest, SubtitleResponse
from app.services.subtitle_service import generate_subtitles

router = APIRouter(prefix="/api/subtitle", tags=["subtitle"])


@router.post("/generate")
async def generate_subtitle(request: SubtitleRequest):
    """
    Generate SRT subtitles from text and duration.
    Splits text by punctuation marks and distributes time evenly.
    """
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if request.duration <= 0:
        raise HTTPException(status_code=400, detail="Duration must be positive")

    try:
        output_path, segment_count = generate_subtitles(
            text=request.text,
            duration=request.duration
        )

        return SubtitleResponse(
            success=True,
            subtitle_path=output_path,
            segment_count=segment_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subtitle generation failed: {str(e)}")