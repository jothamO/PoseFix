# Contributing to PoseFix

Thanks for helping improve PoseFix.

PoseFix is intentionally small and modular. Before adding a new abstraction, ask whether the existing contracts, skill, engine module, or adapter can handle the need without another layer.

## Development setup

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Where changes belong

- **Skills**: domain judgment about pose mechanics, diagnosis, planning, or review.
- **Engine**: deterministic validation, scoring, selection, thresholds, retries, and state.
- **Adapters**: provider-specific request/response translation only.
- **Presets/registries**: shared canonical pose knowledge and vocabularies.
- **Schemas**: stable contracts between components.

A provider-specific field should not be added to a core contract just because one provider supports it.

## Pull requests

Keep PRs focused. Include:

1. the problem being solved;
2. why the change belongs in that layer;
3. tests for behavior changes;
4. any contract or compatibility impact;
5. before/after examples when useful.

Run the full test and lint suite before opening a PR.

## Pose and image examples

Public fixtures must be synthetic, self-owned, or properly licensed. Do not commit private user images, API keys, or provider credentials.

## New presets

A preset should solve a repeatable diagnosed pose problem. It should define supported crops/pose types, required visible regions, mechanics, preservation rules, suppression conditions, and risk. A preset should not exist only because it looks stylish.

## New adapters

Adapters must implement the established adapter boundary and return normalized PoseFix results. Keep vendor parameters inside the adapter.

## Documentation

Public docs should explain the idea before exposing internal schema names. Prefer concrete examples, short sections, and plain language. The `public-docs-writer` skill documents the review pattern used for public-facing material.
