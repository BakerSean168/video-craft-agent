from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, model_validator
from core.models import VideoRequirement


class SceneScript(BaseModel):
    index: int = Field(..., description="分镜序号")
    duration_seconds: int = Field(..., ge=1, description="当前分镜时长")
    subtitle: str = Field(..., description="屏幕字幕")
    voiceover: str = Field(..., description="旁白文案")
    visual_keywords: list[str] = Field(default_factory=list, description="用于素材匹配的关键词")
    source_hint: str = Field(default="uploaded_or_library", description="素材来源建议")


class VideoScript(BaseModel):
    title: str = Field(..., description="视频标题")
    aspect_ratio: str = Field(default="9:16", description="视频比例")
    duration_seconds: int = Field(..., ge=1, description="总时长")
    scenes: list[SceneScript] = Field(..., description="分镜列表")

    @model_validator(mode="after")
    def validate_durations(self) -> "VideoScript":
        if not self.scenes:
            raise ValueError("Video must have at least one scene")
        total_scene_duration = sum(s.duration_seconds for s in self.scenes)
        if total_scene_duration != self.duration_seconds:
            raise ValueError(
                f"Total duration of scenes ({total_scene_duration}s) "
                f"does not match video duration ({self.duration_seconds}s)"
            )
        return self


class UploadedMaterial(BaseModel):
    file_id: str
    original_name: str
    content_type: str
    local_path: str
    size_bytes: int


class MaterialMatch(BaseModel):
    scene_index: int
    material_path: str
    matched_keyword: str | None = None
    source: str  # 'uploaded', 'library', 'fallback'
    fallback_used: bool = False


class RenderResult(BaseModel):
    status: str  # 'success', 'failed'
    output_path: str | None = None
    duration_seconds: int = 0
    format: str = "mp4"
    message: str = ""


class VideoJobStatus(str, Enum):
    queued = "queued"
    upload_saved = "upload_saved"
    calling_dify = "calling_dify"
    script_ready = "script_ready"
    matching_materials = "matching_materials"
    rendering_video = "rendering_video"
    succeeded = "succeeded"
    failed = "failed"


class VideoJob(BaseModel):
    job_id: str
    status: VideoJobStatus = VideoJobStatus.queued
    current_step: str = "任务已创建"
    requirement: VideoRequirement
    uploads: list[UploadedMaterial] = []
    script: VideoScript | None = None
    materials: list[MaterialMatch] = []
    result: RenderResult | None = None
    video_url: str | None = None
    error: str | None = None
