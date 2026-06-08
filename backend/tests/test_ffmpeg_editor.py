import os
import subprocess
import pytest
from pathlib import Path
from tools.ffmpeg_editor import VideoEditor, get_escaped_font_path


@pytest.fixture
def temp_video_generator(tmp_path):
    """Generates a simple color test video with audio using FFmpeg."""
    def _generate(filename="input.mp4", duration=3, width=640, height=360, has_audio=True):
        output_path = tmp_path / filename
        # Generate video using testsrc
        video_filter = f"testsrc=duration={duration}:size={width}x{height}:rate=25"
        
        cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", video_filter]
        
        if has_audio:
            cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", str(duration)]
            cmd += ["-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", str(output_path)]
        else:
            cmd += ["-t", str(duration)]
            cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)]
            
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
        
    return _generate


def test_ffmpeg_editor_trim_and_render(tmp_path, temp_video_generator):
    input_file = temp_video_generator("test_in.mp4", duration=4, has_audio=True)
    output_clip = tmp_path / "clip_out.mp4"
    
    editor = VideoEditor()
    # Trim to 2 seconds, format to 9:16 (using a smaller size for speed in tests, e.g. 540x960)
    editor.trim_and_render_clip(
        input_path=str(input_file),
        output_path=str(output_clip),
        duration=2,
        subtitle="TDD Test Subtitle",
        width=540,
        height=960
    )
    
    assert output_clip.exists()
    # Check duration using ffprobe
    duration = editor.get_duration(str(output_clip))
    assert 1.9 <= duration <= 2.1


def test_ffmpeg_editor_concat(tmp_path, temp_video_generator):
    clip1 = temp_video_generator("clip1.mp4", duration=2, width=540, height=960, has_audio=True)
    clip2 = temp_video_generator("clip2.mp4", duration=3, width=540, height=960, has_audio=True)
    output_final = tmp_path / "final.mp4"
    
    editor = VideoEditor()
    editor.concat_clips(
        clip_paths=[str(clip1), str(clip2)],
        output_path=str(output_final)
    )
    
    assert output_final.exists()
    duration = editor.get_duration(str(output_final))
    assert 4.8 <= duration <= 5.2
