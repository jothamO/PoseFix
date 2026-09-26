from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from posefix.service.app import app
from posefix.service.runtime import STORE

PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZKj8AAAAASUVORK5CYII="
)


def test_health_is_public():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_correction_routes_fail_closed_without_service_key(monkeypatch):
    monkeypatch.delenv("POSEFIX_SERVICE_API_KEY", raising=False)
    monkeypatch.delenv("POSEFIX_SERVICE_ALLOW_UNAUTHENTICATED", raising=False)

    client = TestClient(app)
    response = client.get("/v1/corrections/missing")

    assert response.status_code == 503
    assert response.json()["detail"] == "service_api_key_not_configured"


def test_create_and_get_correction_without_running_provider(monkeypatch):
    monkeypatch.setenv("POSEFIX_SERVICE_API_KEY", "test-secret")
    monkeypatch.setattr(
        "posefix.service.runtime.execute_correction",
        lambda job_id: None,
    )

    client = TestClient(app)
    headers = {"Authorization": "Bearer test-secret"}

    created = client.post(
        "/v1/corrections",
        headers=headers,
        files={"image": ("portrait.png", PNG_1X1, "image/png")},
        data={"intensity": "enhanced"},
    )

    assert created.status_code == 202
    payload = created.json()
    assert payload["status"] == "queued"
    assert payload["intensity"] == "enhanced"

    fetched = client.get(
        f"/v1/corrections/{payload['id']}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == payload["id"]
    assert fetched.json()["status"] == "queued"
    assert fetched.json()["outputs"] == []


def test_invalid_image_content_is_rejected(monkeypatch):
    monkeypatch.setenv("POSEFIX_SERVICE_API_KEY", "test-secret")

    client = TestClient(app)
    response = client.post(
        "/v1/corrections",
        headers={"Authorization": "Bearer test-secret"},
        files={"image": ("fake.png", b"not-an-image", "image/png")},
        data={"intensity": "natural"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid_image_content"


def test_only_passed_outputs_are_downloadable(monkeypatch, tmp_path):
    monkeypatch.setenv("POSEFIX_SERVICE_API_KEY", "test-secret")
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-secret"}

    from posefix.service.runtime import CorrectionJob

    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    passed = output_dir / "a.png"
    failed = output_dir / "b.png"
    passed.write_bytes(PNG_1X1)
    failed.write_bytes(PNG_1X1)

    job = CorrectionJob(
        id="result-job",
        intensity="natural",
        status="completed",
        output_dir=str(output_dir),
        result={
            "generation": {
                "outputs": [
                    {"output_id": "out_001", "variant_id": "option_a", "image_ref": str(passed)},
                    {"output_id": "out_002", "variant_id": "option_b", "image_ref": str(failed)},
                ]
            },
            "reviews": [
                {"decision": "PASS", "overall_score": 0.97},
                {"decision": "RETRY", "overall_score": 0.81},
            ],
        },
    )
    STORE.put(job)

    status_response = client.get("/v1/corrections/result-job", headers=headers)
    outputs = status_response.json()["outputs"]
    assert outputs[0]["download_url"] is not None
    assert outputs[1]["download_url"] is None

    ok = client.get("/v1/corrections/result-job/outputs/out_001", headers=headers)
    bad = client.get("/v1/corrections/result-job/outputs/out_002", headers=headers)
    assert ok.status_code == 200
    assert bad.status_code == 404
