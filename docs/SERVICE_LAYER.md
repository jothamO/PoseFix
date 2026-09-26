# PoseFix Service Layer — M1

The PoseFix service is a thin HTTP boundary around the existing engine. It does not duplicate pose policy.

## Definition of done

M1 is complete only when all five checkpoints pass:

- **M1.1 — HTTP contracts + skeleton**
- **M1.2 — correction job lifecycle**
- **M1.3 — engine/provider integration**
- **M1.4 — security + cleanup + docs**
- **M1.5 — live HTTP provider validation**

The code may be implemented before M1.5, but the milestone is not complete until a real portrait succeeds through the HTTP surface using a live provider.

## Install

```bash
python -m pip install -e '.[openai,service]'
```

## Configuration

Required for correction routes:

```bash
export POSEFIX_SERVICE_API_KEY='replace-with-a-long-random-secret'
export OPENAI_API_KEY='your-provider-key'
```

Optional:

```bash
export POSEFIX_MAX_UPLOAD_BYTES=15728640
export POSEFIX_RETENTION_SECONDS=3600
export POSEFIX_SERVICE_STORAGE=/private/path/posefix-service
export POSEFIX_VISION_MODEL='provider-model-id'
export POSEFIX_IMAGE_MODEL='provider-model-id'
export POSEFIX_REVIEW_MODEL='provider-model-id'
```

Correction routes fail closed if `POSEFIX_SERVICE_API_KEY` is missing. For deliberate local-only development, set `POSEFIX_SERVICE_ALLOW_UNAUTHENTICATED=1`.

## Run locally

```bash
uvicorn posefix.service.app:app --host 127.0.0.1 --port 8000
```

FastAPI exposes the OpenAPI document at `/openapi.json` and interactive docs at `/docs`.

## Create a correction

```bash
curl -X POST http://127.0.0.1:8000/v1/corrections \
  -H "Authorization: Bearer $POSEFIX_SERVICE_API_KEY" \
  -F "image=@portrait.jpg" \
  -F "intensity=enhanced"
```

Example response:

```json
{
  "id": "7a6f...",
  "status": "queued",
  "intensity": "enhanced",
  "status_url": "http://127.0.0.1:8000/v1/corrections/7a6f..."
}
```

## Poll status

```bash
curl http://127.0.0.1:8000/v1/corrections/7a6f... \
  -H "Authorization: Bearer $POSEFIX_SERVICE_API_KEY"
```

Completed outputs are returned separately. A failed review never receives a downloadable image URL.

```json
{
  "id": "7a6f...",
  "status": "completed",
  "intensity": "enhanced",
  "outputs": [
    {
      "output_id": "out_001",
      "variant_id": "option_a",
      "decision": "PASS",
      "overall_score": 0.94,
      "download_url": "/v1/corrections/7a6f.../outputs/out_001"
    },
    {
      "output_id": "out_002",
      "variant_id": "option_b",
      "decision": "PASS",
      "overall_score": 0.92,
      "download_url": "/v1/corrections/7a6f.../outputs/out_002"
    }
  ],
  "error": null
}
```

## Intensity behavior

The service delegates intensity policy to PoseFix itself:

- Natural — 2 separate choices
- Enhanced — 2 separate choices
- Bold — 3 separate choices

The service must never combine alternatives into a contact sheet, collage, split-screen, or comparison image.

## Storage and privacy

The reference service stores source and generated files under a private temporary root. Completed and failed jobs are eligible for deletion after the configured retention period. Cleanup is intentionally simple and in-process for M1.

This is a reference service, not permanent image storage.

## Security boundary

The service:
- accepts only JPEG, PNG, and WebP
- verifies image contents rather than trusting file extensions
- enforces upload limits
- generates unpredictable correction IDs
- never accepts client filesystem paths
- protects correction and output routes with bearer authentication
- exposes only reviewed PASS images for download
- returns sanitized provider/pipeline failures
- does not place provider credentials in API requests or result payloads

Production deployments must terminate TLS in front of the service and use a strong service API key.

## M1.5 live validation

The milestone closes only after recording a real HTTP run:

```text
HTTP client
  -> POST /v1/corrections
  -> PoseFix analysis
  -> plan / target / generation spec
  -> live image provider
  -> live review provider
  -> deterministic PoseFix verdict
  -> GET /v1/corrections/{id}
  -> separate reviewed output image(s)
```

The validation record should capture provider/model identifiers, request identifiers where available, PoseFix contracts, output count, review decisions, and any failure/retry evidence. Never commit API keys or private source images.
