import io
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from core.models import VideoRequirement
from core.schemas import VideoJobStatus
from services.video_pipeline import VideoPipeline, generate_fallback_script
from tools.ffmpeg_editor import escape_text
from api.video_jobs import ALLOWED_EXTENSIONS


def test_generate_fallback_script():
    req = VideoRequirement(
        product_name="AI 编程",
        target_audience="初学者",
        selling_points="简单易学, 7天出作品",
        style="快节奏",
        platform="douyin",
        duration_seconds=15
    )
    script = generate_fallback_script(req)
    assert script["title"] == "AI 编程 - 推广视频"
    assert script["duration_seconds"] == 15
    assert len(script["scenes"]) == 3
    assert script["scenes"][0]["duration_seconds"] == 5
    assert "AI 编程" in script["scenes"][0]["subtitle"]


def test_dify_fallback_in_pipeline(tmp_path, mocker):
    # Setup directories
    pipeline = VideoPipeline(
        library_dir=tmp_path / "assets",
        uploads_dir=tmp_path / "uploads",
        outputs_dir=tmp_path / "outputs",
        jobs_dir=tmp_path / "jobs"
    )

    req = VideoRequirement(
        product_name="AI 编程",
        target_audience="初学者",
        selling_points="简单易学",
        style="快节奏",
        platform="douyin",
        duration_seconds=15
    )

    # Mock DifyClient.run_workflow to raise an exception (dify offline)
    mocker.patch(
        "services.dify_client.DifyClient.run_workflow",
        side_dict=None,
        side_effect=Exception("Dify service unavailable")
    )

    job = pipeline.create_job(req, [])
    # Should run successfully by falling back to local template
    pipeline.run_pipeline_sync(job.job_id)

    updated_job = pipeline.get_job(job.job_id)
    # The pipeline should complete with fallback, although FFmpeg actual render
    # might fail/fallback due to empty libraries, but let's check it doesn't crash
    # because of Dify exception
    assert updated_job.status in (VideoJobStatus.succeeded, VideoJobStatus.failed)
    # If it failed, check that the failure is NOT "Dify service unavailable"
    if updated_job.status == VideoJobStatus.failed:
        assert "Dify service unavailable" not in updated_job.error
    else:
        assert updated_job.script is not None


def test_file_upload_validation():
    client = TestClient(app)

    # 1. Test unsupported file format (txt)
    form_data = {
        "product_name": "TDD App",
        "target_audience": "Developers",
        "selling_points": "High quality code",
        "style": "Modern",
        "platform": "tiktok",
        "duration_seconds": 15,
    }
    files = [
        ("files[]", ("my_hack.txt", io.BytesIO(b"malicious payload"), "text/plain"))
    ]

    response = client.post("/api/video-jobs", data=form_data, files=files)
    assert response.status_code == 400
    assert "unsupported file format" in response.json()["detail"].lower()


def test_subtitle_wrapping():
    from tools.ffmpeg_editor import wrap_text
    
    long_subtitle = "这是一个非常长且超过限制的中文字幕需要我们自动进行换行处理"
    wrapped = wrap_text(long_subtitle, max_chars=12)
    
    assert "\n" in wrapped
    lines = wrapped.split("\n")
    assert len(lines) >= 2
    for line in lines:
        assert len(line) <= 12
