from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .models import CorrectionCreated, CorrectionResponse, ErrorResponse, Intensity
from .runtime import (
    MAX_UPLOAD_BYTES,
    STORE,
    execute_correction,
    new_job,
    output_path,
    public_outputs,
    validate_and_store_upload,
)

bearer = HTTPBearer(auto_error=False)


def _authorize(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ] = None,
) -> None:
    expected = os.getenv("POSEFIX_SERVICE_API_KEY")
    allow_unauthenticated = os.getenv("POSEFIX_SERVICE_ALLOW_UNAUTHENTICATED") == "1"
    if not expected:
        if allow_unauthenticated:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="service_api_key_not_configured",
        )
    supplied = credentials.credentials if credentials and credentials.scheme.lower() == "bearer" else ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")


def create_app() -> FastAPI:
    api = FastAPI(
        title="PoseFix Service",
        version="0.1.0",
        description="HTTP access to the PoseFix pose-correction engine.",
    )

    @api.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post(
        "/v1/corrections",
        response_model=CorrectionCreated,
        status_code=status.HTTP_202_ACCEPTED,
        responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
        dependencies=[Depends(_authorize)],
    )
    async def create_correction(
        request: Request,
        background_tasks: BackgroundTasks,
        image: Annotated[UploadFile, File()],
        intensity: Annotated[Intensity, Form()] = "natural",
    ) -> CorrectionCreated:
        content = await image.read(MAX_UPLOAD_BYTES + 1)
        job = new_job(intensity)
        try:
            validate_and_store_upload(
                job=job,
                content=content,
                content_type=image.content_type,
            )
        except ValueError as exc:
            STORE.update(job.id, status="failed", error=str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from None

        background_tasks.add_task(execute_correction, job.id)
        return CorrectionCreated(
            id=job.id,
            status="queued",
            intensity=intensity,
            status_url=str(request.url_for("get_correction", correction_id=job.id)),
        )

    @api.get(
        "/v1/corrections/{correction_id}",
        response_model=CorrectionResponse,
        responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
        dependencies=[Depends(_authorize)],
        name="get_correction",
    )
    def get_correction(correction_id: str) -> CorrectionResponse:
        STORE.cleanup_expired()
        job = STORE.get(correction_id)
        if not job:
            raise HTTPException(status_code=404, detail="correction_not_found")
        recommendation = None
        if job.result:
            recommendation = job.result.get("recommendation")
            if recommendation is None:
                recommendation = job.result.get("plan", {}).get("recommendation")
        return CorrectionResponse(
            id=job.id,
            status=job.status,
            intensity=job.intensity,
            recommendation=recommendation,
            outputs=public_outputs(job),
            error=job.error,
        )

    @api.get(
        "/v1/corrections/{correction_id}/outputs/{output_id}",
        responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
        dependencies=[Depends(_authorize)],
    )
    def download_output(correction_id: str, output_id: str) -> FileResponse:
        STORE.cleanup_expired()
        job = STORE.get(correction_id)
        if not job:
            raise HTTPException(status_code=404, detail="correction_not_found")
        path = output_path(job, output_id)
        if not path:
            raise HTTPException(status_code=404, detail="output_not_available")
        return FileResponse(path, media_type="image/png", filename=f"{output_id}.png")

    return api


app = create_app()
