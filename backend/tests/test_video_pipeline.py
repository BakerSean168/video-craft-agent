import pytest
from pathlib import Path
from core.models import VideoRequirement
from core.schemas import VideoJobStatus, AssetLibraryItem
from core.frame_models import AssetProfile, VideoMetadata
from services.video_pipeline import VideoPipeline
from unittest.mock import MagicMock


@pytest.fixture
def temp_video_generator(tmp_path):
    import subprocess
    def _generate(filename="input.mp4", duration=3):
        output_path = tmp_path / filename
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"testsrc=duration={duration}:size=640x360:rate=25",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(duration), "-c:v", "libx264", "-c:a", "aac",
            "-pix_fmt", "yuv420p", str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
    return _generate


def test_video_pipeline_run_success(tmp_path, temp_video_generator, mocker):
    # Setup directories
    library_dir = tmp_path / "assets"
    library_dir.mkdir(parents=True, exist_ok=True)
    
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    # Generate source video clip in assets
    src_clip = temp_video_generator("my_test_video.mp4", duration=5)
    
    # Initialize Pipeline
    pipeline = VideoPipeline(
        library_dir=library_dir,
        uploads_dir=uploads_dir,
        outputs_dir=outputs_dir,
        jobs_dir=jobs_dir
    )

    # Save asset to database first
    asset_id = "asset-1"
    asset_profile = AssetProfile(
        asset_id=asset_id,
        original_name="my_test_video.mp4",
        local_path=str(src_clip),
        duration=5.0,
        content_summary="测试视频画面内容",
        tags=["coding"],
        recommended_usage=["hook"],
        segments=[],
        metadata=VideoMetadata(
            duration=5.0,
            width=640,
            height=360,
            fps=25.0,
            has_audio=True,
            aspect_ratio="16:9"
        )
    )
    asset_item = AssetLibraryItem(
        asset_id=asset_id,
        status="completed",
        original_name="my_test_video.mp4",
        local_path=str(src_clip),
        profile=asset_profile
    )
    pipeline.db.save_asset(asset_item)

    # Mock Dify Client
    mock_dify_result = MagicMock()
    mock_dify_result.script = {
        "title": "TDD Pipeline Test",
        "aspect_ratio": "9:16",
        "duration_seconds": 6,
        "timeline": [
            {
                "scene_id": 1,
                "asset_id": "asset-1",
                "source_start": 0.0,
                "source_end": 3.0,
                "start_time": 0.0,
                "end_time": 3.0,
                "subtitle": "Subtitle 1",
                "voiceover": "Voiceover 1",
                "operation": {
                    "speed": 1.0,
                    "crop_mode": "center_crop",
                    "mute_audio": False
                }
            },
            {
                "scene_id": 2,
                "asset_id": "asset-1",
                "source_start": 2.0,
                "source_end": 5.0,
                "start_time": 3.0,
                "end_time": 6.0,
                "subtitle": "Subtitle 2",
                "voiceover": "Voiceover 2",
                "operation": {
                    "speed": 1.0,
                    "crop_mode": "center_crop",
                    "mute_audio": False
                }
            }
        ]
    }
    mocker.patch("services.dify_client.DifyClient.run_workflow", return_value=mock_dify_result)

    requirement = VideoRequirement(
        product_name="AI 编程",
        target_audience="程序员",
        selling_points=["7天出作品"],
        style="紧张刺激",
        platform="抖音",
        duration_seconds=6
    )

    # Create job
    job = pipeline.create_job(requirement, [asset_id])
    assert job.status == VideoJobStatus.queued

    # Execute pipeline synchronously for test
    pipeline.run_pipeline_sync(job.job_id)

    # Fetch job status after completion
    updated_job = pipeline.get_job(job.job_id)
    assert updated_job.status == VideoJobStatus.succeeded
    assert updated_job.dify_success is True
    assert updated_job.result is not None
    assert updated_job.result.status == "success"
    assert Path(updated_job.result.output_path).exists()
