"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# === Asset Models ===

class AssetBase(BaseModel):
    name: str
    type: str  # character_video, action_video, background, product, bgm, font
    tags: Optional[str] = ""
    duration: Optional[float] = 0.0
    width: Optional[int] = 0
    height: Optional[int] = 0


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: int
    path: str
    created_at: datetime

    class Config:
        from_attributes = True


# === Template Models ===

class TemplateBase(BaseModel):
    name: str
    main_video_asset_id: Optional[int] = None
    background_asset_id: Optional[int] = None
    product_asset_id: Optional[int] = None
    bgm_asset_id: Optional[int] = None
    subtitle_style_json: Optional[str] = "{}"
    layout_json: Optional[str] = "{}"
    output_width: Optional[int] = 1080
    output_height: Optional[int] = 1920


class TemplateCreate(TemplateBase):
    pass


class TemplateResponse(TemplateBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# === Project Models ===

class ProjectBase(BaseModel):
    name: str
    template_id: Optional[int] = None
    script_text: Optional[str] = ""
    audio_path: Optional[str] = ""
    subtitle_path: Optional[str] = ""
    output_path: Optional[str] = ""
    status: Optional[str] = "draft"


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# === TTS Models ===

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "zh-CN-XiaoxiaoNeural"
    output_filename: Optional[str] = None


class TTSResponse(BaseModel):
    success: bool
    audio_path: str
    duration: float


# === Subtitle Models ===

class SubtitleRequest(BaseModel):
    text: str
    duration: float
    style_json: Optional[str] = "{}"


class SubtitleResponse(BaseModel):
    success: bool
    subtitle_path: str
    segment_count: int


# === Render Models ===

class RenderRequest(BaseModel):
    project_id: int
    main_video_asset_id: Optional[int] = None
    background_asset_id: Optional[int] = None
    bgm_asset_id: Optional[int] = None
    audio_path: Optional[str] = None
    subtitle_path: Optional[str] = None
    output_width: Optional[int] = 1080
    output_height: Optional[int] = 1920
    layout_json: Optional[str] = None


class RenderResponse(BaseModel):
    success: bool
    output_path: str
    duration: float


# === Settings Models ===

class SettingsRequest(BaseModel):
    ffmpeg_path: Optional[str] = None
    output_directory: Optional[str] = None
    default_voice: Optional[str] = None
    default_resolution: Optional[str] = None


class SettingsResponse(BaseModel):
    ffmpeg_path: str
    output_directory: str
    default_voice: str
    default_resolution: str