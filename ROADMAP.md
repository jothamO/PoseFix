# PoseFix Roadmap

The roadmap is evidence-driven. The active objective is public-launch readiness. Post-launch growth features do not begin until the Before Public Launch gate is green.

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
- review identity, clothing, background, anatomy, subject count, and pose adherence
- record failure cases
- change skills/contracts only where test evidence requires it

## Phase 2 — Before Public Launch gate

The following must be green before public-launch expansion:

### Reliability
- preservation contract implemented and enforced
- machine-readable quality gates
- one targeted retry for failed slots
- failed candidates never surfaced as successful outputs
- PASS-only reviewed output retrieval

### Product surfaces
- reliable CLI
- reliable Python API
- production-ready MCP server/integration
- stable structured request/result contracts
- provider-neutral adapter interface
- at least two working execution paths

### Demonstrability
- difficult benchmark/demo set
- canonical Original -> Reference -> Result examples
- documented failure boundaries
- low-friction demo workflow

### Launch ergonomics
- README optimized for immediate understanding and first success
- install -> configure -> first successful result path minimized
- privacy-conscious telemetry design
- contribution guide and public docs aligned with actual behavior

## Phase 3 — Adapter breadth, only as needed for launch gate

- Gemini adapter
- FLUX adapter
- reference ComfyUI workflow adapter
- capability negotiation tests

Adapter work should be prioritized only when it contributes directly to the launch gate or validates provider neutrality.

## Post-launch, only after gate is green

- broader integration recipes
- Built With PoseFix ecosystem directory
- challenge/community benchmark campaigns
- multi-person support
- live pose coach mode
- optional consumer UI
- automatic provider routing
