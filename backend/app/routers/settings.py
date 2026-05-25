"""
Settings Router - System configuration.
"""
from fastapi import APIRouter, HTTPException

from app.database import get_setting, set_setting
from app.models import SettingsRequest, SettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Default values
DEFAULT_SETTINGS = {
    "ffmpeg_path": "ffmpeg",
    "output_directory": "",
    "default_voice": "zh-CN-XiaoxiaoNeural",
    "default_resolution": "1080x1920"
}


@router.get("")
async def get_settings():
    """Get all system settings."""
    ffmpeg_path = get_setting("ffmpeg_path", DEFAULT_SETTINGS["ffmpeg_path"])
    output_directory = get_setting("output_directory", DEFAULT_SETTINGS["output_directory"])
    default_voice = get_setting("default_voice", DEFAULT_SETTINGS["default_voice"])
    default_resolution = get_setting("default_resolution", DEFAULT_SETTINGS["default_resolution"])

    return SettingsResponse(
        ffmpeg_path=ffmpeg_path,
        output_directory=output_directory,
        default_voice=default_voice,
        default_resolution=default_resolution
    )


@router.post("")
async def update_settings(settings: SettingsRequest):
    """Update system settings."""
    updates = []

    if settings.ffmpeg_path is not None:
        set_setting("ffmpeg_path", settings.ffmpeg_path)
        updates.append("ffmpeg_path")

    if settings.output_directory is not None:
        set_setting("output_directory", settings.output_directory)
        updates.append("output_directory")

    if settings.default_voice is not None:
        set_setting("default_voice", settings.default_voice)
        updates.append("default_voice")

    if settings.default_resolution is not None:
        set_setting("default_resolution", settings.default_resolution)
        updates.append("default_resolution")

    return {
        "success": True,
        "updated": updates
    }