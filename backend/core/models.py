from typing import Any

from pydantic import BaseModel, Field


class VideoRequirement(BaseModel):
    product_name: str = Field(..., min_length=1)
    target_audience: str = Field(..., min_length=1)
    selling_points: str | list[str] = Field(..., min_length=1)
    style: str = "科技感、快节奏"
    platform: str = "douyin"
    duration_seconds: int = Field(default=15, ge=1, le=300)

    def to_dify_inputs(self) -> dict[str, Any]:
        selling_points = self.selling_points
        if isinstance(selling_points, list):
            selling_points = ", ".join(selling_points)

        return {
            "product_name": self.product_name,
            "target_audience": self.target_audience,
            "selling_points": selling_points,
            "style": self.style,
            "platform": self.platform,
            "duration_seconds": self.duration_seconds,
        }


class DifyWorkflowResult(BaseModel):
    task_id: str | None = None
    workflow_run_id: str | None = None
    status: str | None = None
    outputs: dict[str, Any]
    script: Any
