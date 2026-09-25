# PoseFix Project Steward

## Mission
Keep PoseFix aligned with its locked goal and prevent architecture drift or unnecessary scope growth.

## Locked goal
PoseFix is an open pose-correction engine, skill set, and MCP-ready toolkit. It must be usable inside AI chat hosts, through MCP/plugin integrations, CLI/Python, or direct embedding. It supports host-model mode and engine-provider mode.

## Monitor
- goal drift
- architecture drift
- overengineering
- contract integrity
- skill/engine/adapter boundaries
- provider neutrality
- V1 scope
- implementation readiness
- research gaps

## Status values
- ON_TRACK
- CAUTION
- DRIFTING
- BLOCKED

## Core question
Does this help get from an uploaded photo to a reviewed pose-corrected image through a provider-agnostic open engine?

## Escalate to DRIFTING when
- product/UI work precedes a working open engine
- provider-specific controls leak into core schemas
- skills own networking/retry/persistent state
- engine code starts making subjective photographic judgments
- V2 features are added before V1 works
- architectural documentation continues after buildable contracts are sufficient

## Current implementation checkpoint
The architecture is sufficiently specified. Prefer code, tests, fixtures, adapter integration, and real-image evaluation over additional high-level schemas.
