# PoseFix Roadmap

The roadmap is evidence-driven. A later phase should not expand until the current phase has been tested with real outputs.

## Phase 0 — Foundation — complete

- provider-neutral contracts
- ten V1 presets
- deterministic selection and composite planning
- target and generation-spec builders
- normalized result review
- project stewardship rules

## Phase 1 — Service layer + live validation — current

### M1 — PoseFix Service Layer
- M1.1 HTTP contracts + skeleton
- M1.2 correction job lifecycle
- M1.3 engine/provider integration
- M1.4 security + cleanup + docs
- M1.5 live HTTP provider validation

M1 is complete only after a real portrait succeeds through the HTTP service using a live provider.

### Live validation evidence
- run real portrait analysis through a live vision adapter
- run at least one live image-edit provider path
- review identity, clothing, background, anatomy, and pose adherence
- record failure cases
- change skills/contracts only where test evidence requires it

## Phase 2 — Adapter breadth

- Gemini adapter
- FLUX adapter
- reference ComfyUI workflow adapter
- capability negotiation tests

## Phase 3 — Open integration surfaces

- MCP server
- installable skill packaging
- CLI/Python ergonomics
- host-model execution examples

## Later, only if justified

- multi-person support
- live pose coach mode
- optional reference UI
- automatic provider routing
