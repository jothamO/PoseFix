from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Intensity = Literal["natural", "enhanced", "bold"]
JobStatus = Literal["queued", "processing", "completed", "failed"]


class CorrectionCreated(BaseModel):
    id: str
    status: JobStatus
    intensity: Intensity
    status_url: str


class CorrectionOutput(BaseModel):
    output_id: str
    variant_id: str
    decision: Literal["PASS", "RETRY", "FALLBACK", "REJECT"] | None = None
    overall_score: float | None = None
    download_url: str | None = None


class CorrectionResponse(BaseModel):
    id: str
    status: JobStatus
    intensity: Intensity
    recommendation: str | None = None
    outputs: list[CorrectionOutput] = Field(default_factory=list)
    error: str | None = None


class ErrorResponse(BaseModel):
    detail: str
