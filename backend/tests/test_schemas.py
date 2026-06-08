import pytest
from pydantic import ValidationError
from core.schemas import SceneScript, VideoScript


def test_valid_video_script():
    data = {
        "title": "7天变身编程高手！",
        "aspect_ratio": "9:16",
        "duration_seconds": 15,
        "scenes": [
            {
                "index": 1,
                "duration_seconds": 5,
                "subtitle": "你准备好了吗？",
                "voiceover": "加入我们的AI编程训练营，7天后你将完成你的第一个作品！",
                "visual_keywords": ["紧张", "刺激", "编程"],
                "source_hint": "uploaded_or_library"
            },
            {
                "index": 2,
                "duration_seconds": 5,
                "subtitle": "从零开始，快速上手！",
                "voiceover": "无论你是新手还是老手，这里都能让你迅速提升技能！",
                "visual_keywords": ["学习", "编程课程", "快速进步"],
                "source_hint": "uploaded_or_library"
            },
            {
                "index": 3,
                "duration_seconds": 5,
                "subtitle": "挑战极限，成就梦想！",
                "voiceover": "别再犹豫，快来报名吧！7天后，你将成为编程高手！",
                "visual_keywords": ["挑战", "成就", "梦想"],
                "source_hint": "uploaded_or_library"
            }
        ]
    }
    script = VideoScript(**data)
    assert script.title == "7天变身编程高手！"
    assert len(script.scenes) == 3
    assert script.duration_seconds == 15


def test_video_script_duration_mismatch():
    data = {
        "title": "7天变身编程高手！",
        "aspect_ratio": "9:16",
        "duration_seconds": 15,  # Total duration is 15
        "scenes": [
            {
                "index": 1,
                "duration_seconds": 5,
                "subtitle": "Subtitle 1",
                "voiceover": "Voiceover 1",
                "visual_keywords": ["programming"]
            },
            {
                "index": 2,
                "duration_seconds": 8,  # 5 + 8 = 13 (not 15)
                "subtitle": "Subtitle 2",
                "voiceover": "Voiceover 2",
                "visual_keywords": ["programming"]
            }
        ]
    }
    with pytest.raises(ValidationError) as exc_info:
        VideoScript(**data)
    assert "duration" in str(exc_info.value).lower()
