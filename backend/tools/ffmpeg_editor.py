import os
import subprocess
import tempfile
from pathlib import Path


def get_escaped_font_path() -> str | None:
    # Try common Windows font paths first, then fallbacks
    paths = [
        "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simsun.ttc",  # SimSun
        "C:/Windows/Fonts/arial.ttf",   # Arial
    ]
    for p in paths:
        if os.path.exists(p):
            # Escape colon for FFmpeg filter argument
            return p.replace(":", "\\:")
    return None


def escape_text(text: str) -> str:
    # Escape characters for FFmpeg's drawtext filter
    # Backslash, single quotes, colons, commas and percent signs
    t = text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "'\\''").replace(",", "\\,").replace("%", "\\%")
    return t


class VideoEditor:
    def get_duration(self, input_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", check=True)
        return float(result.stdout.strip())

    def has_audio(self, input_path: str) -> bool:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", check=True)
        return len(result.stdout.strip()) > 0

    def trim_and_render_clip(
        self,
        input_path: str,
        output_path: str,
        duration: float,
        subtitle: str,
        width: int = 1080,
        height: int = 1920
    ) -> None:
        escaped_text = escape_text(subtitle)
        font_path = get_escaped_font_path()
        
        # Build drawtext filter part
        drawtext_part = f"drawtext=text='{escaped_text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-150:box=1:boxcolor=black@0.6:boxborderw=10"
        if font_path:
            drawtext_part += f":fontfile='{font_path}'"
            
        video_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{drawtext_part}"
        
        # Determine if source has audio
        source_has_audio = self.has_audio(input_path)
        
        if source_has_audio:
            cmd = [
                "ffmpeg", "-y",
                "-ss", "0",
                "-i", input_path,
                "-t", str(duration),
                "-vf", video_filter,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                "-c:a", "aac",
                "-ar", "44100",
                output_path
            ]
        else:
            # Inject silent audio if source has no audio stream
            cmd = [
                "ffmpeg", "-y",
                "-ss", "0",
                "-i", input_path,
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", str(duration),
                "-vf", video_filter,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                "-c:a", "aac",
                "-ar", "44100",
                output_path
            ]
            
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg trim_and_render_clip failed: {result.stderr}")

    def concat_clips(self, clip_paths: list[str], output_path: str) -> None:
        # Create a temporary file listing the clips to concat
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            temp_txt_path = f.name
            for path in clip_paths:
                # Use forward slashes for compatibility in demuxer file list
                formatted_path = Path(path).resolve().as_posix()
                f.write(f"file '{formatted_path}'\n")
                
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", temp_txt_path,
                "-c", "copy",
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg concat failed: {result.stderr}")
        finally:
            if os.path.exists(temp_txt_path):
                os.remove(temp_txt_path)
