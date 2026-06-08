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


@router.get("/{job_id}/video")
def get_video_file(job_id: str) -> FileResponse:
    job = pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != VideoJobStatus.succeeded or not job.result or not job.result.output_path:
        raise HTTPException(status_code=400, detail="Video is not ready or generation failed")
        
    video_path = Path(job.result.output_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")
        
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename="final.mp4"
    )
