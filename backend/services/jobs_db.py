import sqlite3
import logging
from pathlib import Path
from typing import Optional
from core.schemas import VideoJob

logger = logging.getLogger(__name__)

class VideoJobsDB:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS video_jobs (
                    job_id TEXT PRIMARY KEY,
                    data TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    status TEXT,
                    original_name TEXT,
                    local_path TEXT,
                    data TEXT,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_job(self, job: VideoJob) -> None:
        try:
            job_json = job.model_dump_json()
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO video_jobs (job_id, data) VALUES (?, ?)",
                    (job.job_id, job_json)
                )
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id} to database: {e}")

    def get_job(self, job_id: str) -> Optional[VideoJob]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM video_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return VideoJob.model_validate_json(row["data"])
        except Exception as e:
            logger.error(f"Failed to get job {job_id} from database: {e}")
            return None

    def list_jobs(self, limit: int = 50) -> list[VideoJob]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM video_jobs ORDER BY rowid DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            jobs = []
            for row in rows:
                try:
                    jobs.append(VideoJob.model_validate_json(row["data"]))
                except Exception as parse_err:
                    logger.error(f"Failed to parse job from database: {parse_err}")
            return jobs
        except Exception as e:
            logger.error(f"Failed to list jobs from database: {e}")
            return []

    def save_asset(self, item) -> None:
        try:
            item_json = item.model_dump_json()
            with self.conn:
                self.conn.execute(
                    """
                    INSERT OR REPLACE INTO assets 
                    (asset_id, status, original_name, local_path, data, error) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.asset_id,
                        item.status,
                        item.original_name,
                        item.local_path,
                        item_json,
                        item.error
                    )
                )
        except Exception as e:
            logger.error(f"Failed to save asset {item.asset_id} to database: {e}")

    def get_asset(self, asset_id: str):
        try:
            from core.schemas import AssetLibraryItem
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM assets WHERE asset_id = ?", (asset_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return AssetLibraryItem.model_validate_json(row["data"])
        except Exception as e:
            logger.error(f"Failed to get asset {asset_id} from database: {e}")
            return None

    def list_assets(self) -> list:
        try:
            from core.schemas import AssetLibraryItem
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM assets ORDER BY created_at DESC")
            rows = cursor.fetchall()
            items = []
            for row in rows:
                try:
                    items.append(AssetLibraryItem.model_validate_json(row["data"]))
                except Exception as parse_err:
                    logger.error(f"Failed to parse asset from database: {parse_err}")
            return items
        except Exception as e:
            logger.error(f"Failed to list assets from database: {e}")
            return []

    def delete_asset(self, asset_id: str) -> None:
        try:
            with self.conn:
                self.conn.execute("DELETE FROM assets WHERE asset_id = ?", (asset_id,))
        except Exception as e:
            logger.error(f"Failed to delete asset {asset_id} from database: {e}")
