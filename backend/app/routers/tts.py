"""
TTS Router - Generate text-to-speech audio.
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.models import TTSRequest, TTSResponse
from app.services.tts_service import generate_tts

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/generate")
async def generate_tts_audio(request: TTSRequest):
    """
    Generate TTS audio from text.
    Uses Edge-TTS for high-quality Chinese voice synthesis.
    """
    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        output_path, duration = generate_tts(
            text=request.text,
            voice=request.voice or "zh-CN-XiaoxiaoNeural"
        )

        return TTSResponse(
            success=True,
            audio_path=output_path,
            duration=duration
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.get("/voices")
async def list_voices():
    """List available TTS voices."""
    # Common Chinese voices
    voices = [
        {"name": "zh-CN-XiaoxiaoNeural", "gender": "Female", "language": "zh-CN"},
        {"name": "zh-CN-YunxiNeural", "gender": "Male", "language": "zh-CN"},
        {"name": "zh-CN-YunyangNeural", "gender": "Male", "language": "zh-CN"},
        {"name": "zh-CN-XiaoyiNeural", "gender": "Female", "language": "zh-CN"},
        {"name": "zh-CN-liaoning-XiaobaiNeural", "gender": "Female", "language": "zh-CN"},
        {"name": "zh-CN-shaanxi-XiaobaiNeural", "gender": "Female", "language": "zh-CN"},
    ]
    return {"voices": voices}