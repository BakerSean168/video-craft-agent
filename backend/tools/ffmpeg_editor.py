import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


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


def wrap_text(text: str, max_chars: int = 12) -> str:
    if len(text) <= max_chars:
        return text
        
    # If text contains spaces, we wrap on word boundaries (e.g. English)
    if " " in text:
        words = text.split(" ")
        lines = []
        current_line = []
        current_len = 0
        for w in words:
            if current_len + len(w) + (1 if current_line else 0) <= max_chars:
                current_line.append(w)
                current_len += len(w) + (1 if len(current_line) > 1 else 0)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [w]
                current_len = len(w)
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines)
    else:
        # Character-by-character wrap (e.g. Chinese)
        lines = []
        for i in range(0, len(text), max_chars):
            lines.append(text[i:i+max_chars])
        return "\n".join(lines)


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
        height: int = 1920,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
        speed: float = 1.0,
        mute_audio: bool = False
    ) -> None:
        wrapped_subtitle = wrap_text(subtitle, max_chars=12)
        escaped_text = escape_text(wrapped_subtitle)
        font_path = get_escaped_font_path()
        
        # Build drawtext filter part
        drawtext_part = f"drawtext=text='{escaped_text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-150:box=1:boxcolor=black@0.6:boxborderw=10"
        if font_path:
            drawtext_part += f":fontfile='{font_path}'"
            
        video_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},{drawtext_part}"
        if speed != 1.0:
            video_filter += f",setpts=PTS/{speed}"
            
        # Determine source duration and final output duration
        if end_time is not None:
            source_dur = end_time - start_time
        else:
            source_dur = duration
            
        output_duration = source_dur / speed
        
        # Determine if source has audio and we want to keep it
        use_source_audio = self.has_audio(input_path) and not mute_audio
        
        def get_atempo_filter(s: float) -> str:
            filters = []
            while s > 2.0:
                filters.append("atempo=2.0")
                s /= 2.0
            while s < 0.5:
                filters.append("atempo=0.5")
                s /= 0.5
            if s != 1.0:
                filters.append(f"atempo={s}")
            return ",".join(filters)
            
        if use_source_audio:
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-i", input_path,
                "-t", str(output_duration),
                "-vf", video_filter,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
            ]
            if speed != 1.0:
                cmd.extend(["-filter:a", get_atempo_filter(speed)])
            cmd.extend([
                "-c:a", "aac",
                "-ar", "44100",
                output_path
            ])
        else:
            # Inject silent audio if source has no audio stream or we muted it
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_time),
                "-i", input_path,
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", str(output_duration),
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

    def add_bgm(
        self,
        video_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: float = 0.3,
        video_volume: float = 1.0
    ) -> None:
        has_aud = self.has_audio(video_path)
        
        if has_aud:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", bgm_path,
                "-filter_complex", f"[0:a]volume={video_volume}[a1]; [1:a]volume={bgm_volume}[a2]; [a1][a2]amix=inputs=2:duration=first[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", bgm_path,
                "-filter_complex", f"[1:a]volume={bgm_volume}[a]",
                "-map", "0:v",
                "-map", "[a]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg add_bgm failed: {result.stderr}")

    def convert_format(self, input_path: str, output_path: str, target_format: str) -> None:
        fmt = target_format.lower()
        if fmt == "gif":
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-filter_complex", "[0:v] split [a][b]; [a] palettegen [p]; [b][p] paletteuse",
                output_path
            ]
        elif fmt == "webm":
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-c:v", "libvpx-vp9",
                "-deadline", "realtime",
                "-c:a", "libopus",
                output_path
            ]
        elif fmt == "mov":
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-c:v", "libx264",
                "-c:a", "aac",
                output_path
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                output_path
            ]
            
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg convert_format failed: {result.stderr}")
