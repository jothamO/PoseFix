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

## Validation status

The deterministic and mock pipeline is covered by the test suite. The current milestone is live-provider validation on a real portrait; provider behavior should be treated as experimental until that testing is recorded.

## Intentionally not implemented yet

- multi-person correction
- live camera coach mode
- consumer web UI/authentication
- automatic provider routing
- full Gemini/FLUX/ComfyUI adapters
- production MCP server
