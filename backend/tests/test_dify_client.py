import pytest
from unittest.mock import MagicMock
from core.config import Settings
from services.dify_client import DifyClient
from core.schemas import VideoScript


def test_dify_client_success(mocker):
    # Mock settings
    settings = Settings(
        dify_api_base="https://api.dify.ai/v1",
        dify_api_key="test-key",
        dify_user="test-user",
        dify_script_output_key="script_json",
    )

    # Mock requests.post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "task_id": "task-123",
        "workflow_run_id": "run-456",
        "data": {
            "status": "succeeded",
            "outputs": {
                "script_json": """{
                    "title": "7天变身编程高手！",
                    "aspect_ratio": "9:16",
                    "duration_seconds": 10,
                    "scenes": [
                        {
                            "index": 1,
                            "duration_seconds": 5,
                            "subtitle": "你准备好了吗？",
                            "voiceover": "加入我们的AI编程训练营！",
                            "visual_keywords": ["紧张", "编程"],
                            "source_hint": "uploaded_or_library"
                        },
                        {
                            "index": 2,
                            "duration_seconds": 5,
                            "subtitle": "从零开始！",
                            "voiceover": "快速上手！",
                            "visual_keywords": ["学习"],
                            "source_hint": "uploaded_or_library"
                        }
                    ]
                }"""
            }
        }
    }
    
    mocker.patch("requests.post", return_value=mock_response)

    client = DifyClient.from_settings(settings)
    result = client.run_workflow({"product_name": "AI 编程"})
    
    # Assert
    assert result.task_id == "task-123"
    assert result.workflow_run_id == "run-456"
    assert isinstance(result.script, dict)
    
    # Let's verify we can parse it to VideoScript
    video_script = VideoScript(**result.script)
    assert video_script.title == "7天变身编程高手！"
    assert video_script.duration_seconds == 10
    assert len(video_script.scenes) == 2
