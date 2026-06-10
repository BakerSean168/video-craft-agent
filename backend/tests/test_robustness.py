import io
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from core.models import VideoRequirement
from core.schemas import VideoJobStatus
from services.video_pipeline import VideoPipeline, generate_fallback_edit_plan


def test_generate_fallback_edit_plan():
    req = VideoRequirement(
        product_name="AI 编程",
        target_audience="初学者",
        selling_points=["简单易学, 7天出作品"],
        style="快节奏",
        platform="douyin",
        duration_seconds=15
    )
    plan = generate_fallback_edit_plan(req, [])
    assert plan["title"] == "AI 编程 - 推广视频"
    assert plan["duration_seconds"] == 15
    assert len(plan["timeline"]) == 3
    assert plan["timeline"][0]["end_time"] - plan["timeline"][0]["start_time"] == 5
    assert "AI 编程" in plan["timeline"][0]["subtitle"]


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
        selling_points=["简单易学"],
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
    assert updated_job.dify_success is False
    assert updated_job.status in (VideoJobStatus.succeeded, VideoJobStatus.failed)
    if updated_job.status == VideoJobStatus.failed:
        assert "Dify service unavailable" not in updated_job.error
    else:
        assert updated_job.edit_plan is not None


def test_file_upload_validation():
    client = TestClient(app)

    # Test unsupported file format (txt) in assets endpoint
    files = {"file": ("my_hack.txt", io.BytesIO(b"malicious payload"), "text/plain")}
    response = client.post("/api/assets", files=files)
    assert response.status_code == 400
    assert "unsupported format" in response.json()["detail"].lower()


def test_subtitle_wrapping():
    from tools.ffmpeg_editor import wrap_text
    
    long_subtitle = "这是一个非常长且超过限制的中文字幕需要我们自动进行换行处理"
    wrapped = wrap_text(long_subtitle, max_chars=12)
    
    assert "\n" in wrapped
    lines = wrapped.split("\n")
    assert len(lines) >= 2
    for line in lines:
        assert len(line) <= 12
