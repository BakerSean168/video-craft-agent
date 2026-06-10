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


def test_asset_crud_and_job_pipeline_api(temp_video_generator, mocker):
    client = TestClient(app)

    # 1. Create a dummy video file
    video_file_path = temp_video_generator("my_material.mp4", duration=2)
    with open(video_file_path, "rb") as f:
        file_content = f.read()

    # 2. Upload video asset to the library
    files = {"file": ("my_material.mp4", io.BytesIO(file_content), "video/mp4")}
    upload_resp = client.post("/api/assets", files=files)
    assert upload_resp.status_code == 200
    asset_json = upload_resp.json()
    assert "asset_id" in asset_json
    assert asset_json["status"] in ("analyzing", "completed")
    
    asset_id = asset_json["asset_id"]

    # Poll until asset analysis finishes (since it's a background task)
    max_retries = 30
    asset_analyzed = False
    for _ in range(max_retries):
        get_asset_resp = client.get(f"/api/assets/{asset_id}")
        assert get_asset_resp.status_code == 200
        get_asset_json = get_asset_resp.json()
        if get_asset_json["status"] == "completed":
            asset_analyzed = True
            break
        elif get_asset_json["status"] == "failed":
            pytest.fail(f"Asset analysis failed: {get_asset_json.get('error')}")
        time.sleep(0.5)

    assert asset_analyzed

    # 3. Mock Dify API call in pipeline
    def mock_run_workflow(inputs):
        res = MagicMock()
        res.script = {
            "title": "API Test Video",
            "aspect_ratio": "9:16",
            "duration_seconds": 2,
            "timeline": [
                {
                    "scene_id": 1,
                    "asset_id": asset_id,
                    "source_start": 0.0,
                    "source_end": 2.0,
                    "start_time": 0.0,
                    "end_time": 2.0,
                    "subtitle": "Welcome to TDD",
                    "voiceover": "This is test voiceover",
                    "operation": {
                        "speed": 1.0,
                        "crop_mode": "center_crop",
                        "mute_audio": False
                      }
                }
            ]
        }
        return res
        
    mocker.patch("services.dify_client.DifyClient.run_workflow", side_effect=mock_run_workflow)

    # 4. Create Job using JSON CreateVideoJobRequest
    job_req = {
        "product_name": "TDD App",
        "target_audience": "Developers",
        "selling_points": "High quality code",
        "style": "Modern",
        "platform": "tiktok",
        "duration_seconds": 2,
        "asset_ids": [asset_id]
    }

    response = client.post("/api/video-jobs", json=job_req)
    assert response.status_code == 200
    res_json = response.json()
    assert "job_id" in res_json
    assert res_json["status"] == "queued"
    
    job_id = res_json["job_id"]

    # 5. Poll Job status until completion
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

    # Test asset deletion
    del_resp = client.delete(f"/api/assets/{asset_id}")
    assert del_resp.status_code == 200
    
    # Confirm asset is deleted
    get_del = client.get(f"/api/assets/{asset_id}")
    assert get_del.status_code == 404


def test_list_video_jobs(mocker):
    client = TestClient(app)
    
    from core.schemas import VideoJob, VideoJobStatus
    from core.models import VideoRequirement
    dummy_job = VideoJob(
        job_id="test-list-job-id",
        status=VideoJobStatus.queued,
        requirement=VideoRequirement(
            product_name="Test Product",
            target_audience="Test Audience",
            selling_points=["Test point"],
            style="Test Style",
            platform="douyin",
            duration_seconds=15
        )
    )
    
    mocker.patch("api.video_jobs.pipeline.db.list_jobs", return_value=[dummy_job])
    
    response = client.get("/api/video-jobs")
    assert response.status_code == 200
    res_json = response.json()
    assert isinstance(res_json, list)
    assert len(res_json) == 1
    assert res_json[0]["job_id"] == "test-list-job-id"
