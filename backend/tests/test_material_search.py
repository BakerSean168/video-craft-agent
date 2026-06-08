import pytest
from pathlib import Path
from core.schemas import VideoScript, SceneScript, UploadedMaterial
from tools.material_search import match_materials, MaterialSearcher


def test_match_materials_uploaded_priority(tmp_path):
    # Setup directories
    library_dir = tmp_path / "assets" / "videos"
    library_dir.mkdir(parents=True)
    
    # Create library file
    lib_file = library_dir / "coding.mp4"
    lib_file.touch()

    # Define uploads
    uploads = [
        UploadedMaterial(
            file_id="up-1",
            original_name="my_紧张_clip.mp4",
            content_type="video/mp4",
            local_path=str(tmp_path / "my_紧张_clip.mp4"),
            size_bytes=100
        )
    ]
    
    # Define script
    script = VideoScript(
        title="Test",
        aspect_ratio="9:16",
        duration_seconds=5,
        scenes=[
            SceneScript(
                index=1,
                duration_seconds=5,
                subtitle="Scene 1",
                voiceover="Voiceover 1",
                visual_keywords=["紧张", "coding"],  # Matches both upload (紧张) and library (coding)
                source_hint="uploaded_or_library"
            )
        ]
    )

    searcher = MaterialSearcher(library_dir=library_dir)
    matches = searcher.match_materials(script, uploads)
    
    assert len(matches) == 1
    # Should prefer uploads first
    assert matches[0].source == "uploaded"
    assert matches[0].material_path == str(tmp_path / "my_紧张_clip.mp4")
    assert matches[0].matched_keyword == "紧张"
    assert not matches[0].fallback_used


def test_match_materials_library_fallback(tmp_path):
    library_dir = tmp_path / "assets" / "videos"
    library_dir.mkdir(parents=True)
    
    # Create library file
    lib_file = library_dir / "coding.mp4"
    lib_file.touch()
    
    # Define script (no uploads)
    script = VideoScript(
        title="Test",
        aspect_ratio="9:16",
        duration_seconds=5,
        scenes=[
            SceneScript(
                index=1,
                duration_seconds=5,
                subtitle="Scene 1",
                voiceover="Voiceover 1",
                visual_keywords=["coding"],
                source_hint="uploaded_or_library"
            )
        ]
    )

    searcher = MaterialSearcher(library_dir=library_dir)
    matches = searcher.match_materials(script, [])
    
    assert len(matches) == 1
    assert matches[0].source == "library"
    assert matches[0].material_path == str(lib_file)
    assert matches[0].matched_keyword == "coding"
    assert not matches[0].fallback_used


def test_match_materials_fallback_default(tmp_path):
    library_dir = tmp_path / "assets" / "videos"
    library_dir.mkdir(parents=True)
    
    # Create fallback file
    default_file = library_dir / "default.mp4"
    default_file.touch()
    
    # Define script (keywords don't match anything)
    script = VideoScript(
        title="Test",
        aspect_ratio="9:16",
        duration_seconds=5,
        scenes=[
            SceneScript(
                index=1,
                duration_seconds=5,
                subtitle="Scene 1",
                voiceover="Voiceover 1",
                visual_keywords=["unknown_keyword"],
                source_hint="uploaded_or_library"
            )
        ]
    )

    searcher = MaterialSearcher(library_dir=library_dir)
    matches = searcher.match_materials(script, [])
    
    assert len(matches) == 1
    assert matches[0].source == "fallback"
    assert matches[0].material_path == str(default_file)
    assert matches[0].fallback_used
