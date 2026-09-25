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
- Project Steward agent
- Public Docs Writer skill
- GitHub Maintainer agent
- professional community-health files and GitHub issue/PR templates
- CI configuration for Python 3.11-3.13
- Dependabot configuration
- public GitHub repository publication

## Validation status

The deterministic and mock pipeline was validated locally before publication with 7 passing tests and successful Python bytecode compilation. GitHub CI is configured to independently run Ruff and the test suite. Live-provider behavior remains experimental until a real portrait is run through analysis -> planning -> generation -> review.

## Intentionally not implemented yet

- multi-person correction
- live camera coach mode
- consumer web UI/authentication
- automatic provider routing
- full Gemini/FLUX/ComfyUI adapters
- production MCP server
