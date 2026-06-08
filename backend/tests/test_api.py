import io
import time
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
from core.schemas import VideoJobStatus


@pytest.fixture
def temp_video_generator(tmp_path):
    import subprocess
    def _generate(filename="input.mp4", duration=2):
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
    return _generate


def test_create_and_poll_job_api(temp_video_generator, mocker):
    client = TestClient(app)

    # 1. Create a dummy video file
    video_file_path = temp_video_generator("my_material.mp4", duration=2)
    with open(video_file_path, "rb") as f:
        file_content = f.read()

    # 2. Mock Dify API call in pipeline
    mock_dify_result = MagicMock()
    mock_dify_result.script = {
        "title": "API Test Video",
        "aspect_ratio": "9:16",
        "duration_seconds": 2,
        "scenes": [
            {
                "index": 1,
                "duration_seconds": 2,
                "subtitle": "Welcome to TDD",
                "voiceover": "This is test voiceover",
                "visual_keywords": ["material"],
                "source_hint": "uploaded_or_library"
            }
        ]
    }
    mocker.patch("services.dify_client.DifyClient.run_workflow", return_value=mock_dify_result)

    # 3. Call POST /api/video-jobs
    form_data = {
        "product_name": "TDD App",
        "target_audience": "Developers",
        "selling_points": "High quality code",
        "style": "Modern",
        "platform": "tiktok",
        "duration_seconds": 2,
    }
    files = [
        ("files[]", ("my_material.mp4", io.BytesIO(file_content), "video/mp4"))
    ]

    response = client.post("/api/video-jobs", data=form_data, files=files)
    assert response.status_code == 200
    res_json = response.json()
    assert "job_id" in res_json
    assert res_json["status"] == "queued"
    
    job_id = res_json["job_id"]

    # Since it runs in the background, we need to poll the status
    max_retries = 30
    succeeded = False
    for _ in range(max_retries):
        status_resp = client.get(f"/api/video-jobs/{job_id}")
        assert status_resp.status_code == 200
        status_json = status_resp.json()
        
        if status_json["status"] == VideoJobStatus.succeeded:
            succeeded = True
            break
        elif status_json["status"] == VideoJobStatus.failed:
            pytest.fail(f"Job failed with error: {status_json.get('error')}")
            
        time.sleep(0.5)

    assert succeeded

    # Check video retrieval
    video_resp = client.get(f"/api/video-jobs/{job_id}/video")
    assert video_resp.status_code == 200
    assert video_resp.headers["content-type"] == "video/mp4"
    assert len(video_resp.content) > 0
