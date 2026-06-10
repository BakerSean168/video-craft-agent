import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from core.models import VideoRequirement
from core.schemas import VideoJob, VideoJobStatus, CreateVideoJobRequest
from services.video_pipeline import VideoPipeline
from pydantic import BaseModel

class ConvertRequest(BaseModel):
    target_format: str

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video-jobs", tags=["video-jobs"])
pipeline = VideoPipeline()


@router.get("")
def list_video_jobs(limit: int = 50) -> list[VideoJob]:
    return pipeline.db.list_jobs(limit)


@router.post("")
def create_video_job(
    request: CreateVideoJobRequest,
    background_tasks: BackgroundTasks
) -> dict:
    # Split selling points if comma separated, otherwise wrap in list
    points = [p.strip() for p in request.selling_points.split(",") if p.strip()]
    if not points:
        points = [request.selling_points]

    requirement = VideoRequirement(
        product_name=request.product_name,
        target_audience=request.target_audience,
        selling_points=points,
        style=request.style,
        platform=request.platform,
        duration_seconds=request.duration_seconds
    )

    # Initialize job in pipeline using selected asset_ids from library
    job = pipeline.create_job(requirement, request.asset_ids)
    
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
