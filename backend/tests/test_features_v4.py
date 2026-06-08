import io
import os
import subprocess
from pathlib import Path
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from core.schemas import VideoJobStatus
from tools.ffmpeg_editor import VideoEditor


@pytest.fixture
def temp_media_generator(tmp_path):
    """Generates mock media files for testing."""
    def _generate_video(filename="video.mp4", duration=2):
        output_path = tmp_path / filename
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"testsrc=duration={duration}:size=320x240:rate=25",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(duration), "-c:v", "libx264", "-c:a", "aac",
            "-pix_fmt", "yuv420p", str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

    def _generate_audio(filename="music.wav", duration=3):
        output_path = tmp_path / filename
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"sine=frequency=440:duration={duration}",
            "-t", str(duration), str(output_path)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

    return _generate_video, _generate_audio


def test_ffmpeg_editor_add_bgm(temp_media_generator, tmp_path):
    gen_video, gen_audio = temp_media_generator
    video_file = gen_video("test_v.mp4", duration=3)
    bgm_file = gen_audio("test_bgm.wav", duration=4)
    output_mixed = tmp_path / "mixed_v.mp4"

    editor = VideoEditor()
    editor.add_bgm(
        video_path=str(video_file),
        bgm_path=str(bgm_file),
        output_path=str(output_mixed),
        bgm_volume=0.3,
        video_volume=0.8
    )

    assert output_mixed.exists()
    assert editor.get_duration(str(output_mixed)) > 0.0
    assert editor.has_audio(str(output_mixed))


def test_ffmpeg_editor_conversion(temp_media_generator, tmp_path):
    gen_video, _ = temp_media_generator
    video_file = gen_video("test_v.mp4", duration=2)
    
    editor = VideoEditor()
    
    # 1. Convert to gif
    output_gif = tmp_path / "out.gif"
    editor.convert_format(str(video_file), str(output_gif), "gif")
    assert output_gif.exists()
    
    # 2. Convert to webm
    output_webm = tmp_path / "out.webm"
    editor.convert_format(str(video_file), str(output_webm), "webm")
    assert output_webm.exists()


def test_api_convert_endpoint(temp_media_generator, mocker, tmp_path):
    gen_video, _ = temp_media_generator
    client = TestClient(app)

    # 1. Setup mock pipeline job
    from services.video_pipeline import _JOBS_DB, VideoPipeline
    from core.models import VideoRequirement
    from core.schemas import VideoJob, RenderResult

    pipeline = VideoPipeline(
        library_dir=tmp_path / "assets",
        uploads_dir=tmp_path / "uploads",
        outputs_dir=tmp_path / "outputs",
        jobs_dir=tmp_path / "jobs"
    )
    
    req = VideoRequirement(
        product_name="BGM App",
        target_audience="Devs",
        selling_points="Nice feature",
        style="Clean",
        platform="tiktok",
        duration_seconds=2
    )
    
    job = pipeline.create_job(req, [])
    # Put a mock succeeded final video
    final_video = gen_video("final.mp4", duration=2)
    # Move the final video to job's output directory
    job_output_path = Path(pipeline.outputs_dir) / job.job_id / "final.mp4"
    job_output_path.parent.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(str(final_video), str(job_output_path))
    
    job.status = VideoJobStatus.succeeded
    job.result = RenderResult(
        status="success",
        output_path=str(job_output_path),
        duration_seconds=2,
        format="mp4",
        message="video ready"
    )
    
    # Register in DB
    _JOBS_DB[job.job_id] = job

    # 2. Call Convert Endpoint
    convert_data = {"target_format": "gif"}
    response = client.post(f"/api/video-jobs/{job.job_id}/convert", json=convert_data)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["job_id"] == job.job_id
    assert res_json["target_format"] == "gif"
    assert "download_url" in res_json
    
    download_url = res_json["download_url"]
    
    # 3. Download converted file
    dl_resp = client.get(download_url)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] in ("image/gif", "video/gif")
    assert len(dl_resp.content) > 0
