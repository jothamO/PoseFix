from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from ..adapters import OpenAIImageAdapter, OpenAIReviewAdapter, OpenAIVisionAdapter
from ..pipeline import analyze_and_plan, generate_and_review

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_UPLOAD_BYTES = int(os.getenv("POSEFIX_MAX_UPLOAD_BYTES", str(15 * 1024 * 1024)))
RETENTION_SECONDS = int(os.getenv("POSEFIX_RETENTION_SECONDS", "3600"))


@dataclass
class CorrectionJob:
    id: str
    intensity: str
    status: str = "queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    source_path: str | None = None
    output_dir: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, CorrectionJob] = {}
        self._lock = threading.Lock()

    def put(self, job: CorrectionJob) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> CorrectionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def cleanup_expired(self) -> None:
        cutoff = time.time() - RETENTION_SECONDS
        expired: list[CorrectionJob] = []
        with self._lock:
            for job_id, job in list(self._jobs.items()):
                if job.created_at < cutoff and job.status in {"completed", "failed"}:
                    expired.append(self._jobs.pop(job_id))
        for job in expired:
            if job.source_path:
                shutil.rmtree(Path(job.source_path).parent, ignore_errors=True)


STORE = JobStore()
STORAGE_ROOT = Path(
    os.getenv(
        "POSEFIX_SERVICE_STORAGE",
        str(Path(tempfile.gettempdir()) / "posefix-service"),
    )
)


def new_job(intensity: str) -> CorrectionJob:
    STORE.cleanup_expired()
    job_id = uuid.uuid4().hex
    job_dir = STORAGE_ROOT / job_id
    output_dir = job_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=False)
    job = CorrectionJob(id=job_id, intensity=intensity, output_dir=str(output_dir))
    STORE.put(job)
    return job


def validate_and_store_upload(
    *,
    job: CorrectionJob,
    content: bytes,
    content_type: str | None,
) -> str:
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError("unsupported_image_type")
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("invalid_image_size")

    job_dir = Path(job.output_dir or "").parent
    candidate = job_dir / "source.upload"
    candidate.write_bytes(content)

    try:
        with Image.open(candidate) as image:
            detected = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        candidate.unlink(missing_ok=True)
        raise ValueError("invalid_image_content") from None

    if detected not in ALLOWED_FORMATS:
        candidate.unlink(missing_ok=True)
        raise ValueError("unsupported_image_type")

    suffix = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}[detected]
    source = candidate.with_suffix(suffix)
    candidate.replace(source)
    STORE.update(job.id, source_path=str(source))
    return str(source)


def _adapter_models() -> tuple[OpenAIVisionAdapter, OpenAIImageAdapter, OpenAIReviewAdapter]:
    vision_model = os.getenv("POSEFIX_VISION_MODEL")
    image_model = os.getenv("POSEFIX_IMAGE_MODEL")
    review_model = os.getenv("POSEFIX_REVIEW_MODEL")
    return (
        OpenAIVisionAdapter(model=vision_model) if vision_model else OpenAIVisionAdapter(),
        OpenAIImageAdapter(model=image_model) if image_model else OpenAIImageAdapter(),
        OpenAIReviewAdapter(model=review_model) if review_model else OpenAIReviewAdapter(),
    )


def execute_correction(job_id: str) -> None:
    job = STORE.get(job_id)
    if not job or not job.source_path or not job.output_dir:
        return

    STORE.update(job_id, status="processing")
    try:
        vision, image, reviewer = _adapter_models()
        planned = analyze_and_plan(
            source_image_path=job.source_path,
            vision_adapter=vision,
            intensity=job.intensity,
        )
        if not planned.get("generation_spec"):
            STORE.update(
                job_id,
                status="completed",
                result={
                    "recommendation": planned.get("plan", {}).get(
                        "recommendation", "preserve_original"
                    ),
                    "generation": None,
                    "reviews": [],
                },
            )
            return

        result = generate_and_review(
            source_image_path=job.source_path,
            planned=planned,
            image_adapter=image,
            review_adapter=reviewer,
            output_dir=job.output_dir,
        )
        generation = result.get("generation") or {}
        if generation.get("generation_status") not in {"success", "partial_success"}:
            STORE.update(job_id, status="failed", error="provider_or_pipeline_error")
            return

        STORE.update(job_id, status="completed", result=result)
    except Exception:  # noqa: BLE001 - service boundary sanitizes provider failures
        STORE.update(job_id, status="failed", error="provider_or_pipeline_error")


def public_outputs(job: CorrectionJob) -> list[dict[str, Any]]:
    if not job.result:
        return []
    generation = job.result.get("generation") or {}
    generated = generation.get("outputs", [])
    reviews = job.result.get("reviews", [])

    outputs: list[dict[str, Any]] = []
    for index, item in enumerate(generated):
        review = reviews[index] if index < len(reviews) else {}
        decision = review.get("decision")
        output_id = item.get("output_id", f"out_{index + 1:03d}")
        outputs.append(
            {
                "output_id": output_id,
                "variant_id": item.get("variant_id", f"option_{index + 1}"),
                "decision": decision,
                "overall_score": review.get("overall_score"),
                "download_url": (
                    f"/v1/corrections/{job.id}/outputs/{output_id}"
                    if decision == "PASS"
                    else None
                ),
            }
        )
    return outputs


def output_path(job: CorrectionJob, output_id: str) -> Path | None:
    if not job.result or not job.output_dir:
        return None
    generation = job.result.get("generation") or {}
    reviews = job.result.get("reviews", [])
    for index, item in enumerate(generation.get("outputs", [])):
        if item.get("output_id") != output_id:
            continue
        review = reviews[index] if index < len(reviews) else {}
        if review.get("decision") != "PASS":
            return None
        candidate = Path(item.get("image_ref", "")).resolve()
        root = Path(job.output_dir).resolve()
        if root not in candidate.parents or not candidate.is_file():
            return None
        return candidate
    return None
