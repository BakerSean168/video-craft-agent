import os
import base64
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from core.frame_models import (
    VideoMetadata, FrameInfo, FrameAnalysis, AssetSegment, AssetProfile
)

logger = logging.getLogger(__name__)

class FrameService:
    def __init__(self, analyzer_url: str) -> None:
        self.analyzer_url = analyzer_url.rstrip("/")

    def get_video_metadata(self, video_path: str) -> VideoMetadata:
        """Use ffprobe to extract video metadata."""
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,avg_frame_rate,duration",
            "-show_entries", "format=duration",
            "-of", "json",
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", check=True)
            data = json.loads(result.stdout)
            
            # Extract values from streams or format
            stream = data.get("streams", [{}])[0]
            fmt = data.get("format", {})
            
            # Width & Height
            width = int(stream.get("width", 1080))
            height = int(stream.get("height", 1920))
            
            # FPS
            avg_frame_rate = stream.get("avg_frame_rate", "25/1")
            if "/" in avg_frame_rate:
                num, den = avg_frame_rate.split("/")
                fps = float(num) / float(den) if float(den) != 0 else 25.0
            else:
                fps = float(avg_frame_rate) if avg_frame_rate else 25.0
                
            # Duration
            duration_str = stream.get("duration") or fmt.get("duration")
            duration = float(duration_str) if duration_str else 0.0
            
            # Aspect ratio
            aspect_ratio = "9:16"
            if width > 0 and height > 0:
                ratio = width / height
                if abs(ratio - 16/9) < 0.1:
                    aspect_ratio = "16:9"
                elif abs(ratio - 9/16) < 0.1:
                    aspect_ratio = "9:16"
                elif abs(ratio - 1/1) < 0.1:
                    aspect_ratio = "1:1"
                else:
                    aspect_ratio = f"{width}:{height}"
            
            # Audio presence check
            has_audio = self._has_audio(video_path)
            
            return VideoMetadata(
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                has_audio=has_audio,
                aspect_ratio=aspect_ratio
            )
        except Exception as e:
            logger.error(f"Failed to get video metadata via ffprobe for {video_path}: {e}")
            # Fallback metadata
            return VideoMetadata(
                duration=10.0,
                width=1080,
                height=1920,
                fps=25.0,
                has_audio=False,
                aspect_ratio="9:16"
            )

    def _has_audio(self, video_path: str) -> bool:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", check=True)
            return len(result.stdout.strip()) > 0
        except Exception:
            return False

    def extract_key_frames(
        self,
        video_path: str,
        asset_id: str,
        output_dir: Path,
        interval: float = 3.0,
        max_frames: int = 10
    ) -> List[FrameInfo]:
        """Extract keyframes at regular intervals using FFmpeg."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean existing frames in output_dir
        for f in output_dir.glob("frame_*.jpg"):
            try:
                f.unlink()
            except Exception:
                pass
                
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"fps=1/{interval}",
            "-vsync", "vfr",
            str(output_dir / "frame_%03d.jpg")
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except Exception as e:
            logger.error(f"FFmpeg frame extraction failed: {e}")
            return []
            
        # Collect extracted frames
        frame_files = sorted(list(output_dir.glob("frame_*.jpg")))
        frames = []
        
        # Limit frames if needed
        frame_files = frame_files[:max_frames]
        
        for idx, f_path in enumerate(frame_files):
            # Frame index is 1-indexed, so frame k is at (k-1) * interval
            timestamp = idx * interval
            frame_id = f"{asset_id}_f{idx+1:03d}"
            frames.append(
                FrameInfo(
                    frame_id=frame_id,
                    asset_id=asset_id,
                    timestamp=timestamp,
                    image_path=str(f_path)
                )
            )
            
        return frames

    def analyze_frame(self, frame: FrameInfo) -> FrameAnalysis:
        """Call the Cloudflare Worker to analyze a single frame."""
        try:
            if not os.path.exists(frame.image_path):
                raise FileNotFoundError(f"Frame image not found: {frame.image_path}")
                
            with open(frame.image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
                
            payload = {
                "image": encoded_image,
                "frame_id": frame.frame_id,
                "asset_id": frame.asset_id,
                "timestamp": frame.timestamp
            }
            
            response = requests.post(
                f"{self.analyzer_url}/analyze-frame",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if not data.get("ok") or "frame_analysis" not in data:
                raise ValueError(f"Worker response is missing frame_analysis or not OK: {data}")
                
            analysis_data = data["frame_analysis"]
            return FrameAnalysis(**analysis_data)
        except Exception as e:
            logger.error(f"Failed to analyze frame {frame.frame_id}: {e}")
            # Return fallback DEFAULT_FRAME_ANALYSIS with error details
            return FrameAnalysis(description_cn="未能识别画面内容", error=str(e))

    def get_secondary_summary(self, descriptions: List[str]) -> str:
        """Call Cloudflare Worker summarize endpoint to get a single unified summary."""
        if not descriptions:
            return "无画面内容描述"
        try:
            payload = {"descriptions": descriptions}
            response = requests.post(
                f"{self.analyzer_url}/summarize",
                json=payload,
                timeout=20
            )
            response.raise_for_status()
            data = response.json()
            if data.get("ok") and "summary" in data:
                return data["summary"]
            else:
                logger.warning(f"Summarize response is not ok or missing summary: {data}")
        except Exception as e:
            logger.error(f"Failed to call summarize endpoint: {e}")
            
        # Fallback to local concatenation of first few unique descriptions
        unique_desc = []
        for desc in descriptions:
            if desc and desc not in unique_desc:
                unique_desc.append(desc)
        return "；".join(unique_desc[:3])

    def analyze_asset(
        self,
        video_path: str,
        asset_id: str,
        output_frames_dir: Path,
        max_frames: int = 8
    ) -> AssetProfile:
        """Full asset profiling flow: metadata -> keyframes -> worker analysis -> summarization -> segments."""
        logger.info(f"Starting profiling for asset {asset_id} (path: {video_path})")
        
        metadata = self.get_video_metadata(video_path)
        
        # Calculate dynamic interval to fit max_frames
        interval = max(3.0, metadata.duration / max_frames)
        
        frames = self.extract_key_frames(
            video_path=video_path,
            asset_id=asset_id,
            output_dir=output_frames_dir,
            interval=interval,
            max_frames=max_frames
        )
        
        analyses: List[FrameAnalysis] = []
        descriptions: List[str] = []
        all_tags = set()
        recommended_usages = set()
        
        for frame in frames:
            analysis = self.analyze_frame(frame)
            analyses.append(analysis)
            if analysis.description_cn:
                descriptions.append(analysis.description_cn)
            for tag in analysis.tags:
                all_tags.add(tag)
            if analysis.marketing_role and analysis.marketing_role not in {"filler", "other"}:
                recommended_usages.add(analysis.marketing_role)
                
        # Run LLM secondary summarization (Option B)
        content_summary = self.get_secondary_summary(descriptions)
        
        # Build segments based on scene_environment transition
        segments: List[AssetSegment] = []
        
        if analyses and frames:
            current_segment_frames = []
            current_segment_analyses = []
            
            for idx, (frame, analysis) in enumerate(zip(frames, analyses)):
                if not current_segment_frames:
                    current_segment_frames.append(frame)
                    current_segment_analyses.append(analysis)
                else:
                    prev_analysis = current_segment_analyses[-1]
                    # If scene environment changes, split segment
                    if prev_analysis.scene_environment != analysis.scene_environment:
                        # Close current segment
                        segment_id = f"{asset_id}_seg{len(segments)+1}"
                        segments.append(
                            self._create_segment(
                                segment_id=segment_id,
                                frames=current_segment_frames,
                                analyses=current_segment_analyses,
                                next_start=frame.timestamp
                            )
                        )
                        current_segment_frames = [frame]
                        current_segment_analyses = [analysis]
                    else:
                        current_segment_frames.append(frame)
                        current_segment_analyses.append(analysis)
                        
            # Close the last segment
            if current_segment_frames:
                segment_id = f"{asset_id}_seg{len(segments)+1}"
                segments.append(
                    self._create_segment(
                        segment_id=segment_id,
                        frames=current_segment_frames,
                        analyses=current_segment_analyses,
                        next_start=metadata.duration
                    )
                )
        
        return AssetProfile(
            asset_id=asset_id,
            original_name=os.path.basename(video_path),
            local_path=video_path,
            duration=metadata.duration,
            content_summary=content_summary,
            tags=list(all_tags),
            recommended_usage=list(recommended_usages),
            segments=segments,
            metadata=metadata,
            frames=frames,
            frame_analyses=analyses
        )


    def _create_segment(
        self,
        segment_id: str,
        frames: List[FrameInfo],
        analyses: List[FrameAnalysis],
        next_start: float
    ) -> AssetSegment:
        start = frames[0].timestamp
        end = next_start
        
        # Concatenate descriptions for summary
        desc_list = [a.description_cn for a in analyses if a.description_cn]
        summary = "；".join(desc_list) if desc_list else "画面转场过渡"
        
        # Collect tags
        tags = set()
        marketing_roles = {}
        total_quality = 0.0
        
        for a in analyses:
            for tag in a.tags:
                tags.add(tag)
            r = a.marketing_role
            marketing_roles[r] = marketing_roles.get(r, 0) + 1
            total_quality += a.quality_score
            
        # Determine dominant marketing role
        dominant_role = "filler"
        if marketing_roles:
            dominant_role = max(marketing_roles, key=marketing_roles.get)
            
        avg_quality = total_quality / len(analyses) if analyses else 0.5
        
        return AssetSegment(
            segment_id=segment_id,
            start=start,
            end=end,
            summary=summary,
            tags=list(tags),
            marketing_role=dominant_role,
            quality_score=avg_quality
        )
