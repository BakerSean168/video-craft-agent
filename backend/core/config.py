import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    dify_api_base: str
    dify_api_key: str
    dify_user: str
    dify_script_output_key: str
    frame_analyzer_url: str = "https://video-frame-analyzer.bakersean.workers.dev"


def get_settings() -> Settings:
    return Settings(
        dify_api_base=os.getenv("DIFY_API_BASE", "https://api.dify.ai/v1").rstrip("/"),
        dify_api_key=os.getenv("DIFY_API_KEY", ""),
        dify_user=os.getenv("DIFY_USER", "video-craft-demo-user"),
        dify_script_output_key=os.getenv("DIFY_SCRIPT_OUTPUT_KEY", "script_json"),
        frame_analyzer_url=os.getenv("FRAME_ANALYZER_URL", "https://video-frame-analyzer.bakersean.workers.dev"),
    )
