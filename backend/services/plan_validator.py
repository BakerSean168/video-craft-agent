import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def validate_edit_plan(edit_plan_data: Any, asset_map: Dict[str, Any], requirement_duration: int) -> List[str]:
    """
    Validate the edit plan for safety, completeness, and logical consistency.
    Modifies the edit_plan_data in place (if it is a dict or mutable object) to clamp/correct minor issues.
    Returns a list of warning messages.
    Raises ValueError for fatal errors.
    """
    warnings = []
    
    # 1. Handle Pydantic or Dict inputs
    if hasattr(edit_plan_data, "dict"):
        timeline = edit_plan_data.timeline
        duration_seconds = edit_plan_data.duration_seconds
    elif isinstance(edit_plan_data, dict):
        timeline = edit_plan_data.get("timeline", [])
        duration_seconds = edit_plan_data.get("duration_seconds", 0)
    else:
        raise ValueError(f"Invalid edit plan type: {type(edit_plan_data)}")
        
    if not timeline:
        raise ValueError("Edit plan contains no timeline scenes.")
        
    # Sort timeline by start_time just in case
    # Convert Pydantic objects to dicts for uniform validation if they are objects
    scenes = []
    for s in timeline:
        if not isinstance(s, dict):
            # Convert Pydantic to dict or get attributes
            scenes.append({
                "scene_id": getattr(s, "scene_id"),
                "asset_id": getattr(s, "asset_id"),
                "source_start": getattr(s, "source_start"),
                "source_end": getattr(s, "source_end"),
                "start_time": getattr(s, "start_time"),
                "end_time": getattr(s, "end_time"),
                "subtitle": getattr(s, "subtitle", ""),
                "voiceover": getattr(s, "voiceover", ""),
                "operation": getattr(s, "operation", None)
            })
        else:
            scenes.append(s)
            
    # Sort by start_time
    scenes.sort(key=lambda x: x.get("start_time", 0.0))
    
    # 2. Check asset existence and clamp boundaries
    for idx, scene in enumerate(scenes):
        asset_id = scene.get("asset_id")
        scene_id = scene.get("scene_id", idx + 1)
        
        if asset_id not in asset_map:
            raise ValueError(f"Scene {scene_id} references non-existent asset_id: {asset_id}")
            
        asset = asset_map[asset_id]
        # Get asset duration (might be in asset.duration or dict asset["duration"])
        asset_duration = getattr(asset, "duration", None)
        if asset_duration is None:
            if isinstance(asset, dict):
                asset_duration = asset.get("duration", 0.0)
            else:
                asset_duration = 0.0
                
        source_start = float(scene.get("source_start", 0.0))
        source_end = float(scene.get("source_end", 0.0))
        
        if source_start < 0:
            warnings.append(f"Scene {scene_id}: source_start ({source_start}s) is negative. Clamped to 0.0s.")
            scene["source_start"] = 0.0
            source_start = 0.0
            
        if source_end <= source_start:
            raise ValueError(f"Scene {scene_id}: source_end ({source_end}s) must be greater than source_start ({source_start}s).")
            
        # If source_end exceeds asset duration, clamp with tolerance
        if source_end > asset_duration:
            diff = source_end - asset_duration
            if diff <= 1.0: # 1 second tolerance for rounding
                warnings.append(f"Scene {scene_id}: source_end ({source_end}s) slightly exceeds asset {asset_id} duration ({asset_duration}s). Clamped.")
                scene["source_end"] = asset_duration
                source_end = asset_duration
            else:
                raise ValueError(f"Scene {scene_id}: source_end ({source_end}s) exceeds asset {asset_id} duration ({asset_duration}s) beyond tolerance.")
                
    # 3. Check and correct timeline continuity and start/end sync
    expected_start = 0.0
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", idx + 1)
        start_time = float(scene.get("start_time", 0.0))
        end_time = float(scene.get("end_time", 0.0))
        
        # Check start_time continuity
        if abs(start_time - expected_start) > 0.1:
            warnings.append(f"Scene {scene_id}: Timeline gap detected. Adjusting start_time from {start_time}s to {expected_start}s.")
            scene["start_time"] = expected_start
            start_time = expected_start
            
        # Calculate expected output duration of clip
        source_duration = scene["source_end"] - scene["source_start"]
        operation = scene.get("operation")
        speed = 1.0
        if operation:
            if hasattr(operation, "speed"):
                speed = float(operation.speed)
            elif isinstance(operation, dict):
                speed = float(operation.get("speed", 1.0))
                
        if speed <= 0:
            speed = 1.0
            if isinstance(operation, dict):
                operation["speed"] = 1.0
            elif operation:
                operation.speed = 1.0
                
        expected_output_duration = source_duration / speed
        
        # Validate sync between source trim duration and output clip duration
        current_output_duration = end_time - start_time
        if abs(current_output_duration - expected_output_duration) > 0.2:
            # Sync by adjusting end_time
            new_end_time = start_time + expected_output_duration
            warnings.append(
                f"Scene {scene_id}: Trim duration ({source_duration}s at {speed}x speed = {expected_output_duration:.2f}s) "
                f"does not match clip duration ({current_output_duration:.2f}s). Adjusting end_time to {new_end_time:.2f}s."
            )
            scene["end_time"] = new_end_time
            end_time = new_end_time
            
        expected_start = end_time
        
    # Write back changes to Pydantic objects if needed
    if not isinstance(edit_plan_data, dict) and hasattr(edit_plan_data, "timeline"):
        for orig, validated in zip(edit_plan_data.timeline, scenes):
            orig.source_start = validated["source_start"]
            orig.source_end = validated["source_end"]
            orig.start_time = validated["start_time"]
            orig.end_time = validated["end_time"]
            if orig.operation and hasattr(orig.operation, "speed") and "operation" in validated and isinstance(validated["operation"], dict):
                orig.operation.speed = validated["operation"]["speed"]
        
        # Update total duration_seconds
        edit_plan_data.duration_seconds = int(round(expected_start))
        
    # 4. Check total duration compared to requirement
    total_duration = expected_start
    if abs(total_duration - requirement_duration) > 3.0:
        warnings.append(f"Total output duration ({total_duration:.1f}s) deviates from required duration ({requirement_duration}s).")
        
    # 5. Check subtitles
    for idx, scene in enumerate(scenes):
        scene_id = scene.get("scene_id", idx + 1)
        sub = scene.get("subtitle", "").strip()
        if not sub:
            warnings.append(f"Scene {scene_id} has an empty subtitle.")
            
    return warnings
