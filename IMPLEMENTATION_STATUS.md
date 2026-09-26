# Implementation status

## Version
0.3.0 development snapshot

## Implemented

- versioned provider-neutral contracts
- ten canonical V1 presets
- deterministic preset scoring and composite selection
- pose-target and generation-spec builders
- generation result normalization
- review decision logic
- mock vision, generation, and review paths
- early OpenAI vision/image/review adapter boundaries
- CLI planning and analysis paths
- HTTP service layer skeleton with correction creation/status/output routes
- in-process correction job lifecycle
- upload type/size/content validation and temporary private storage
- bearer-protected correction routes with fail-closed configuration
- reviewed PASS-only output downloads
- Project Steward agent
- Public Docs Writer skill
- GitHub Maintainer agent
- professional community-health files and GitHub issue/PR templates
- CI configuration for Python 3.11-3.13
- Dependabot configuration
- public GitHub repository publication

## Validation status

The deterministic and mock pipeline is covered by automated tests and GitHub CI. The M1 HTTP service implementation is now under validation. Live-provider behavior remains experimental until a real portrait is run through HTTP -> analysis -> planning -> generation -> review -> reviewed output retrieval.

M1 is not complete until M1.5 live HTTP provider validation passes.

## Intentionally not implemented yet

- multi-person correction
- live camera coach mode
- consumer web UI/authentication
- automatic provider routing
- full Gemini/FLUX/ComfyUI adapters
- production MCP server
