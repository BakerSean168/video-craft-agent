from enum import Enum
from typing import Any, Optional, List
from pydantic import BaseModel, Field, model_validator
from core.models import VideoRequirement
from core.frame_models import AssetProfile


# EditPlan structures for structured editing decisions
class EditSceneOperation(BaseModel):
    speed: float = Field(default=1.0, description="播放速度")
    crop_mode: Optional[str] = Field(default="center_crop", description="裁剪模式")
    mute_audio: bool = Field(default=False, description="是否静音")


class EditScene(BaseModel):
    scene_id: int = Field(..., description="分镜ID")
    asset_id: str = Field(..., description="使用的素材资源ID")
    source_start: float = Field(..., description="素材裁剪开始时间（秒）")
    source_end: float = Field(..., description="素材裁剪结束时间（秒）")
    start_time: float = Field(..., description="在输出视频中的开始时间")
    end_time: float = Field(..., description="在输出视频中的结束时间")
    subtitle: str = Field(..., description="该场景屏幕字幕")
    voiceover: Optional[str] = Field(default=None, description="旁白文案")
    transition: Optional[str] = Field(default=None, description="转场效果")
    operation: EditSceneOperation = Field(default_factory=EditSceneOperation, description="剪辑参数")


class EditPlan(BaseModel):
    title: str = Field(..., description="视频标题")
    aspect_ratio: str = Field(default="9:16", description="视频比例")
    duration_seconds: int = Field(..., description="视频总时长")
    timeline: list[EditScene] = Field(..., description="时间轴分镜序列")
    warnings: list[str] = Field(default_factory=list, description="生成过程中的警告")

    @model_validator(mode="after")
    def validate_timeline(self) -> "EditPlan":
        if not self.timeline:
            raise ValueError("EditPlan must have at least one edit scene in the timeline")
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
    analyzing_assets = "analyzing_assets"
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
    assets: list[AssetProfile] = []
    edit_plan: EditPlan | None = None
    materials: list[MaterialMatch] = []
    result: RenderResult | None = None
    video_url: str | None = None
    error: str | None = None
    dify_success: bool | None = None


class AssetLibraryItem(BaseModel):
    asset_id: str
    status: str  # 'analyzing' | 'completed' | 'failed'
    original_name: str
    local_path: str
    profile: Optional[AssetProfile] = None
    error: Optional[str] = None


class CreateVideoJobRequest(BaseModel):
    product_name: str
    target_audience: str
    selling_points: str
    style: str
    platform: str
    duration_seconds: int
    asset_ids: list[str]

