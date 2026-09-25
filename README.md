# PoseFix

> **Fix the pose, keep the photo.**

PoseFix is an early open-source reference engine for correcting the pose in an existing single-person photo while trying to preserve the person, clothing, background, lighting, and photographic moment.

It is not a photo editor UI and it is not tied to one AI provider. PoseFix separates pose reasoning from orchestration and from the model that actually renders the edit.

## Why PoseFix exists

A photo can be almost right: good expression, good outfit, good location, awkward posture. PoseFix is built around a simple rule:

**Make the smallest pose change that solves the problem. Preserve everything that already works.**

Instead of asking an image model to "make this look better," PoseFix analyzes the pose, identifies what should be preserved, chooses a safe correction plan, turns that plan into a provider-neutral generation request, and reviews the result.

## How it works

```text
photo
  ↓
pose analysis
  ↓
what works / what should change
  ↓
preset + composite selection
  ↓
pose target
  ↓
provider-neutral generation spec
  ↓
OpenAI / Gemini / FLUX / ComfyUI / host model
  ↓
result review
  ↓
PASS / RETRY / FALLBACK / REJECT
```

The architecture follows one rule:

**Skills reason. Engine governs. Adapters translate.**

- **Skills** contain pose knowledge and review logic.
- **Engine** handles deterministic selection, validation, thresholds, retries, and state.
- **Adapters** translate the normalized contracts into provider-specific calls.

## Current V1 scope

PoseFix currently targets:

- one primary person
- an existing photo rather than live camera capture
- subtle-to-moderate pose correction
- ten canonical pose presets
- deterministic preset/composite planning
- provider-neutral JSON contracts
- a review loop with `PASS`, `RETRY`, `FALLBACK`, and `REJECT`

Not in V1: multi-person editing, live camera coaching, a hosted consumer web app, authentication, marketplace features, or automatic provider routing.

## Quick start

Requires Python 3.11+.

```bash
python -m pip install -e '.[dev]'
pytest
```

Try the deterministic fixture path:

```bash
posefix analyze examples/test-portrait/placeholder.jpg \
  --vision-provider mock \
  --fixture examples/test-portrait/pose_analysis.json
```

Plan from an existing normalized analysis:

```bash
posefix plan examples/test-portrait/pose_analysis.json
```

## Providers

PoseFix is designed for two modes:

### Host-model mode

An AI host can use the PoseFix skills and contracts while performing vision or generation with its own capabilities.

### Engine-provider mode

PoseFix calls a configured provider adapter. The reference repo currently includes mock adapters and an early OpenAI adapter boundary. Other adapters can implement the same interface without changing the core engine.

For live OpenAI use, configure your own API credentials:

```bash
export OPENAI_API_KEY='...'
```

Never commit API keys or private photos to the repository.

## Core contracts

The normalized pipeline is built around versioned schemas in [`schemas/`](schemas/):

- `pose_analysis.v1`
- `composite_plan.v1`
- `pose_target.v1`
- `generation_spec.v1`
- `generation_result.v1`
- `result_review.v1`

These contracts are intentionally provider-neutral.

## Canonical V1 presets

PoseFix ships with ten initial presets in [`posefix/presets/`](posefix/presets/): Straighten Up, Relaxed Upright, Open Shoulders, Chin & Gaze Fix, Soft Weight Shift, One Hand Purpose, Turned Slightly, Casual Confidence, Professional Presence, and Editorial Lite.

"Natural Upgrade" is not a preset. It is a presentation label for a safe composite of compatible corrections selected for a particular image.

## Project status

PoseFix is **pre-release research software**. The normalized contracts, deterministic selector, composite planner, target/spec builders, mock pipeline, and review decision logic are implemented. Live provider validation is the next evidence-gathering milestone.

See [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) and [`ROADMAP.md`](ROADMAP.md).

## Contributing

Contributions are welcome, especially around pose mechanics, test fixtures, provider adapters, preservation/review quality, and documentation. Start with [`CONTRIBUTING.md`](CONTRIBUTING.md).

Please use synthetic, self-owned, or properly licensed images in public tests and examples.

## Security

Do not open public issues for credential leaks or security vulnerabilities. See [`SECURITY.md`](SECURITY.md) for the reporting process.

## License

MIT. See [`LICENSE`](LICENSE).
