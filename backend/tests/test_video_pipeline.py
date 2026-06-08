import pytest
from pathlib import Path
from core.models import VideoRequirement
from core.schemas import VideoJobStatus, UploadedMaterial
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

    # Generate source video clip in uploads
    src_clip = temp_video_generator("my_test_video.mp4", duration=5)
    upload_file = UploadedMaterial(
        file_id="upload-1",
        original_name="my_紧张_video.mp4",
        content_type="video/mp4",
        local_path=str(src_clip),
        size_bytes=src_clip.stat().st_size
    )

    # Mock Dify Client
    mock_dify_result = MagicMock()
    mock_dify_result.script = {
        "title": "TDD Pipeline Test",
        "aspect_ratio": "9:16",
        "duration_seconds": 6,
        "scenes": [
            {
                "index": 1,
                "duration_seconds": 3,
                "subtitle": "Subtitle 1",
                "voiceover": "Voiceover 1",
                "visual_keywords": ["紧张"],
                "source_hint": "uploaded_or_library"
            },
            {
                "index": 2,
                "duration_seconds": 3,
                "subtitle": "Subtitle 2",
                "voiceover": "Voiceover 2",
                "visual_keywords": ["紧张"],
                "source_hint": "uploaded_or_library"
            }
        ]
    }
    mocker.patch("services.dify_client.DifyClient.run_workflow", return_value=mock_dify_result)

    requirement = VideoRequirement(
        product_name="AI 编程",
        target_audience="程序员",
        selling_points="7天出作品",
        style="紧张刺激",
        platform="抖音",
        duration_seconds=6
    )

    # Initialize Pipeline
    pipeline = VideoPipeline(
        library_dir=library_dir,
        uploads_dir=uploads_dir,
        outputs_dir=outputs_dir,
        jobs_dir=jobs_dir
    )

    # Create job
    job = pipeline.create_job(requirement, [upload_file])
    assert job.status == VideoJobStatus.queued

    # Execute pipeline synchronously for test
    pipeline.run_pipeline_sync(job.job_id)

    # Fetch job status after completion
    updated_job = pipeline.get_job(job.job_id)
    assert updated_job.status == VideoJobStatus.succeeded
    assert updated_job.result is not None
    assert updated_job.result.status == "success"
    assert Path(updated_job.result.output_path).exists()
