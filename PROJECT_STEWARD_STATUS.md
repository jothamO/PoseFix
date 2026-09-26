# Project Steward status

**Status:** ON_TRACK  
**Drift risk:** LOW  
**Phase:** pre-public-launch readiness

## Current assessment

PoseFix has a working provider-neutral foundation, a service-layer implementation in progress, public repository structure, and deterministic/mock coverage. The project is now explicitly optimizing for public-launch readiness rather than broad architecture expansion.

## Current objective

Do not advance into post-launch growth work until every item in the Before Public Launch gate is green.

### Before Public Launch gate

- preservation contract implemented and enforced
- machine-readable quality gates for identity, clothing, background, anatomy, subject count, and pose adherence
- one targeted retry for failed slots; failed results are not surfaced as successful outputs
- live-provider validation through HTTP -> analysis -> planning -> generation -> review -> PASS-only retrieval
- difficult public demo/benchmark set
- canonical README centered on outcome and first success
- reliable CLI path
- reliable Python API
- production-ready MCP integration
- provider abstraction with at least two working execution paths
- stable structured result contract with review/retry metadata
- privacy-conscious telemetry design
- demo workflow for zero-code/low-friction evaluation
- contribution guide aligned with current implementation

## Guardrail

Prioritize in this order:

1. reliable correction quality
2. first-success ergonomics
3. embeddability
4. demonstrability
5. distribution readiness

Do not add multi-person support, live camera coaching, automatic provider routing, or broad consumer UI work until the gate above is green.

## Next evidence milestone

Complete M1.5 live provider validation using a real portrait, record observed failure modes, and use that evidence to finish the preservation/quality/retry requirements without unnecessary architecture expansion.
