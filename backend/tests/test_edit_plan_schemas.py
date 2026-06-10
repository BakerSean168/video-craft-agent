import pytest
from pydantic import ValidationError
from core.schemas import EditPlan, EditScene, EditSceneOperation
from services.plan_validator import validate_edit_plan
from core.models import VideoRequirement

def test_edit_plan_validation_success():
    data = {
        "title": "AI编程训练营",
        "aspect_ratio": "9:16",
        "duration_seconds": 10,
        "timeline": [
            {
                "scene_id": 1,
                "asset_id": "asset_1",
                "source_start": 0.0,
                "source_end": 5.0,
                "start_time": 0.0,
                "end_time": 5.0,
                "subtitle": "字幕1",
                "voiceover": "旁白1",
                "operation": {
                    "speed": 1.0,
                    "crop_mode": "center_crop",
                    "mute_audio": False
                }
            },
            {
                "scene_id": 2,
                "asset_id": "asset_1",
                "source_start": 5.0,
                "source_end": 10.0,
                "start_time": 5.0,
                "end_time": 10.0,
                "subtitle": "字幕2",
                "voiceover": "旁白2",
                "operation": {
                    "speed": 1.0,
                    "crop_mode": "center_crop",
                    "mute_audio": False
                }
            }
        ]
    }
    
    plan = EditPlan(**data)
    assert plan.title == "AI编程训练营"
    assert len(plan.timeline) == 2
    assert plan.duration_seconds == 10
    
    asset_map = {
        "asset_1": {
            "duration": 15.0,
            "asset_id": "asset_1"
        }
    }
    
    warnings = validate_edit_plan(plan, asset_map, 10)
    assert len(warnings) == 0

def test_plan_validator_clamping_and_corrections():
    data = {
        "title": "Clamp Test",
        "aspect_ratio": "9:16",
        "duration_seconds": 15,
        "timeline": [
            {
                "scene_id": 1,
                "asset_id": "asset_1",
                "source_start": -1.0, # should clamp to 0
                "source_end": 11.5,   # slightly exceeds duration (10s) + tolerance (1.0s), wait let's test within tolerance first: 10.5
                "start_time": 0.0,
                "end_time": 5.0,      # doesn't match trim duration at 1.0x speed, should adjust end_time
                "subtitle": "",       # empty subtitle warning
                "operation": {"speed": 1.0, "mute_audio": False}
            }
        ]
    }
    
    plan = EditPlan(**data)
    asset_map = {
        "asset_1": {
            "duration": 10.0,
            "asset_id": "asset_1"
        }
    }
    
    # We set source_end to 10.5, which exceeds duration by 0.5s (within 1s tolerance)
    plan.timeline[0].source_end = 10.5
    
    warnings = validate_edit_plan(plan, asset_map, 15)
    
    # Check clamping and corrections
    assert plan.timeline[0].source_start == 0.0
    assert plan.timeline[0].source_end == 10.0
    assert plan.timeline[0].start_time == 0.0
    # Expected output duration = (10.0 - 0.0) / 1.0 = 10.0
    assert plan.timeline[0].end_time == 10.0
    
    # Validate warnings
    warning_texts = "".join(warnings)
    assert "negative" in warning_texts
    assert "exceeds" in warning_texts
    assert "adjusting end_time" in warning_texts.lower()
    assert "empty subtitle" in warning_texts.lower()
