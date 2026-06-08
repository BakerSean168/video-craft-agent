import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from core.models import VideoRequirement
from core.schemas import UploadedMaterial, VideoJob, VideoJobStatus
from services.video_pipeline import VideoPipeline

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

router = APIRouter(prefix="/api/video-jobs", tags=["video-jobs"])
pipeline = VideoPipeline()


@router.post("")
def create_video_job(
    background_tasks: BackgroundTasks,
    product_name: str = Form("AI 编程训练营"),
    target_audience: str = Form("想转行 AI 的程序员"),
    selling_points: str = Form("零基础入门 AI Agent, 带项目实战, 适合 Python 初学者"),
    style: str = Form("科技感、快节奏"),
    platform: str = Form("douyin"),
    duration_seconds: int = Form(15),
    files: list[UploadFile] = File(default=[], alias="files[]")
) -> dict:
    # Split selling points if comma separated, otherwise wrap in list
    points = [p.strip() for p in selling_points.split(",") if p.strip()]
    if not points:
        points = [selling_points]

    requirement = VideoRequirement(
        product_name=product_name,
        target_audience=target_audience,
        selling_points=points,
        style=style,
        platform=platform,
        duration_seconds=duration_seconds
    )

    # Initialize job in pipeline
    job = pipeline.create_job(requirement, [])
    
    # Save uploaded files if any
    uploads = []
    if files:
        # Validate all files first
        for f in files:
            if not f.filename:
                continue
            ext = Path(f.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")
            if hasattr(f, "size") and f.size and f.size > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File size exceeds the 100MB limit")

        job_upload_dir = pipeline.uploads_dir / job.job_id
        job_upload_dir.mkdir(parents=True, exist_ok=True)
        
        for f in files:
            if not f.filename:
                continue
            file_path = job_upload_dir / f.filename
            
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
                
            uploads.append(
                UploadedMaterial(
                    file_id=str(uuid.uuid4()),
                    original_name=f.filename,
                    content_type=f.content_type or "video/mp4",
                    local_path=str(file_path),
                    size_bytes=file_path.stat().st_size
                )
            )
            
    # Update job with uploaded materials details
    job.uploads = uploads
    job.status = VideoJobStatus.upload_saved
    job.current_step = "上传素材已保存"
    
    # Put job status back to queued before running background task
    job.status = VideoJobStatus.queued
    
    # Trigger the background pipeline run
    background_tasks.add_task(pipeline.run_pipeline_sync, job.job_id)

    return {
        "job_id": job.job_id,
        "status": job.status,
        "message": "任务已创建"
    }


@router.get("/{job_id}")
def get_video_job(job_id: str) -> VideoJob:
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


from pydantic import BaseModel

class ConvertRequest(BaseModel):
    target_format: str


@router.post("/{job_id}/convert")
def convert_video_job_format(job_id: str, request: ConvertRequest) -> dict:
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != VideoJobStatus.succeeded or not job.result or not job.result.output_path:
        raise HTTPException(status_code=400, detail="Original video is not ready")
        
    target_fmt = request.target_format.lower().strip()
    if target_fmt not in {"gif", "webm", "mov", "mp4"}:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {target_fmt}")
        
    original_path = Path(job.result.output_path)
    target_path = original_path.with_suffix(f".{target_fmt}")
    
    if not target_path.exists():
        from tools.ffmpeg_editor import VideoEditor
        try:
            editor = VideoEditor()
            editor.convert_format(str(original_path), str(target_path), target_fmt)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
            
    return {
        "job_id": job_id,
        "target_format": target_fmt,
        "download_url": f"/api/video-jobs/{job_id}/video?format={target_fmt}"
    }


@router.get("/{job_id}/video")
def get_video_file(job_id: str, format: Optional[str] = None) -> FileResponse:
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != VideoJobStatus.succeeded or not job.result or not job.result.output_path:
        raise HTTPException(status_code=400, detail="Video is not ready or generation failed")
        
    original_path = Path(job.result.output_path)
    
    if format:
        target_fmt = format.lower().strip()
        file_path = original_path.with_suffix(f".{target_fmt}")
        if not file_path.exists():
            raise HTTPException(status_code=400, detail=f"Format {target_fmt} is not converted yet. Please call /convert first.")
        
        media_types = {
            "gif": "image/gif",
            "webm": "video/webm",
            "mov": "video/quicktime",
            "mp4": "video/mp4"
        }
        media_type = media_types.get(target_fmt, "application/octet-stream")
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=f"final.{target_fmt}"
        )
        
    if not original_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")
        
    return FileResponse(
        path=str(original_path),
        media_type="video/mp4",
        filename="final.mp4"
    )
