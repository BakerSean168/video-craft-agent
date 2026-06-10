from typing import List, Optional
from pydantic import BaseModel, Field

class VideoMetadata(BaseModel):
    duration: float = Field(..., description="视频总时长（秒）")
    width: int = Field(..., description="视频宽度")
    height: int = Field(..., description="视频高度")
    fps: float = Field(..., description="视频帧率")
    has_audio: bool = Field(..., description="是否含有音频流")
    aspect_ratio: str = Field(..., description="视频宽高比，例如 '9:16' 或 '16:9'")

class FrameInfo(BaseModel):
    frame_id: str = Field(..., description="帧的唯一ID")
    asset_id: str = Field(..., description="对应视频素材ID")
    timestamp: float = Field(..., description="帧在视频中的时间戳（秒）")
    image_path: str = Field(..., description="帧图像在本地的暂存路径")

class FrameAnalysis(BaseModel):
    description_cn: str = Field(default="未能识别画面内容", description="中文画面描述")
    description_en: Optional[str] = Field(default=None, description="英文画面描述")
    shot_type: str = Field(default="other", description="镜头类型")
    main_subject: Optional[str] = Field(default=None, description="主体描述")
    objects: List[str] = Field(default_factory=list, description="检测到的物体列表")
    human_presence: str = Field(default="none", description="人物出现状态")
    product_visibility: str = Field(default="none", description="产品可见度")
    scene_environment: str = Field(default="other", description="场景环境")
    action: Optional[str] = Field(default=None, description="动作描述")
    visual_quality: str = Field(default="medium", description="画质主观评估")
    quality_score: float = Field(default=0.5, description="画质客观评分 0.0 - 1.0")
    marketing_role: str = Field(default="filler", description="营销角色/视频用途")
    editing_suggestion: Optional[str] = Field(default=None, description="剪辑使用建议")
    tags: List[str] = Field(default_factory=list, description="画面标签")
    people_count: int = Field(default=0, description="画面中人类的数量")
    text_on_screen: List[str] = Field(default_factory=list, description="画面中的OCR文字")

class AssetSegment(BaseModel):
    segment_id: str = Field(..., description="片段唯一ID")
    start: float = Field(..., description="片段开始时间（秒）")
    end: float = Field(..., description="片段结束时间（秒）")
    summary: str = Field(..., description="片段画面及内容中文摘要")
    tags: List[str] = Field(default_factory=list, description="片段特征标签")
    marketing_role: str = Field(default="filler", description="片段最适宜的营销角色")
    quality_score: float = Field(default=0.5, description="片段平均画质评分")

class AssetProfile(BaseModel):
    asset_id: str = Field(..., description="素材唯一ID")
    original_name: str = Field(..., description="素材原始文件名")
    local_path: str = Field(..., description="素材本地绝对路径")
    duration: float = Field(..., description="视频总时长（秒）")
    content_summary: str = Field(..., description="整段视频的高质量中文摘要总结")
    tags: List[str] = Field(default_factory=list, description="视频标签汇总")
    recommended_usage: List[str] = Field(default_factory=list, description="推荐视频用途列表")
    segments: List[AssetSegment] = Field(default_factory=list, description="视频语义分段")
    metadata: VideoMetadata = Field(..., description="视频详细元数据")
