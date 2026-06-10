import uuid
import shutil
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from core.schemas import AssetLibraryItem
from services.video_pipeline import VideoPipeline

logger = logging.getLogger(__name__)

# Initialize pipeline
pipeline = VideoPipeline()

# Define assets directory
backend_dir = Path(__file__).resolve().parents[1]
project_dir = backend_dir.parent
assets_dir = project_dir / "storage" / "assets"
assets_dir.mkdir(parents=True, exist_ok=True)

# Define allowed extensions and size limit (100MB)
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
MAX_FILE_SIZE = 100 * 1024 * 1024

router = APIRouter(prefix="/api/assets", tags=["assets"])


def analyze_asset_task(asset_id: str, file_path: str, original_name: str) -> None:
    frames_dir = assets_dir / f"{asset_id}_frames"
    try:
        logger.info(f"Starting background asset analysis for {asset_id}")
        
        # Invoke frame service to run frame extraction and LLM analysis
        profile = pipeline.frame_service.analyze_asset(
            video_path=file_path,
            asset_id=asset_id,
            output_frames_dir=frames_dir
        )
        # Update original name to match upload
        profile.original_name = original_name
        
        # Save completed item
        item = AssetLibraryItem(
            asset_id=asset_id,
            status="completed",
            original_name=original_name,
            local_path=file_path,
            profile=profile
        )
        pipeline.db.save_asset(item)
        logger.info(f"Asset analysis completed successfully for {asset_id}")
        
    except Exception as e:
        logger.error(f"Failed to analyze asset {asset_id}: {e}")
        if frames_dir.exists():
            try:
                shutil.rmtree(frames_dir)
            except Exception:
                pass
        item = AssetLibraryItem(
            asset_id=asset_id,
            status="failed",
            original_name=original_name,
            local_path=file_path,
            error=str(e)
        )
        pipeline.db.save_asset(item)



@router.get("")
def list_assets() -> list[AssetLibraryItem]:
    return pipeline.db.list_assets()


@router.post("")
def upload_asset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> AssetLibraryItem:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
        
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")
        
    # Generate asset ID and determine save path
    asset_id = str(uuid.uuid4())
    save_path = assets_dir / f"{asset_id}{ext}"
    
    try:
        # Save uploaded file
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")
        
    # Check file size limit
    file_size = save_path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(status_code=400, detail="File size exceeds the 100MB limit")

    # Create analyzing DB item
    item = AssetLibraryItem(
        asset_id=asset_id,
        status="analyzing",
        original_name=file.filename,
        local_path=str(save_path)
    )
    pipeline.db.save_asset(item)
    
    # Trigger background analysis task
    background_tasks.add_task(
        analyze_asset_task,
        asset_id=asset_id,
        file_path=str(save_path),
        original_name=file.filename
    )
    
    return item


@router.get("/{asset_id}")
def get_asset(asset_id: str) -> AssetLibraryItem:
    item = pipeline.db.get_asset(asset_id)
    if not item:
        raise HTTPException(status_code=404, detail="Asset not found")
    return item


@router.delete("/{asset_id}")
def delete_asset(asset_id: str) -> dict:
    item = pipeline.db.get_asset(asset_id)
    if not item:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    # Delete DB record
    pipeline.db.delete_asset(asset_id)
    
    # Delete physical file
    file_path = Path(item.local_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete physical file {file_path}: {e}")
            
    # Delete physical frames directory
    frames_dir = assets_dir / f"{asset_id}_frames"
    if frames_dir.exists():
        try:
            shutil.rmtree(frames_dir)
        except Exception as e:
            logger.warning(f"Failed to delete frames directory {frames_dir}: {e}")
            
    return {"message": "素材已删除", "asset_id": asset_id}


@router.get("/{asset_id}/video")
def get_asset_video(asset_id: str) -> FileResponse:
    item = pipeline.db.get_asset(asset_id)
    if not item:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    file_path = Path(item.local_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical video file not found")
        
    # Guess media type
    ext = file_path.suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime"
    }
    media_type = media_types.get(ext, "video/mp4")
    return FileResponse(path=str(file_path), media_type=media_type)


@router.get("/{asset_id}/frames/{frame_id}")
def get_asset_frame(asset_id: str, frame_id: str) -> FileResponse:
    frames_dir = (assets_dir / f"{asset_id}_frames").resolve()
    if not frames_dir.exists():
        raise HTTPException(status_code=404, detail="Frames directory not found")
        
    parts = frame_id.split("_f")
    if len(parts) != 2 or not parts[1].isdigit():
        raise HTTPException(status_code=400, detail="Invalid frame ID format")
        
    file_name = f"frame_{parts[1]}.jpg"
    file_path = (frames_dir / file_name).resolve()
    
    if not file_path.is_relative_to(frames_dir):
        raise HTTPException(status_code=400, detail="Invalid path traversal attempt")
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Frame image not found: {file_name}")
        
    return FileResponse(path=str(file_path), media_type="image/jpeg")

