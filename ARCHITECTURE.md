# PoseFix architecture

## Foundational rule
**Skills reason. Engine governs. Adapters translate.**

## Runtime pipeline

```text
IMAGE
  -> pose analysis / mechanics / diagnosis skill stage
  -> deterministic preset + composite selection
  -> pose_target.v1
  -> generation_spec.v1
  -> provider adapter or host model
  -> generation_result.v1
  -> result review skill
  -> PASS / RETRY / FALLBACK / REJECT
```

## V1 execution optimization
The eight logical skills may be executed as four model stages:

1. ANALYZE: pose-analysis + pose-mechanics + pose-diagnosis
2. PLAN: preset recommendation + target builder + generation planner
3. GENERATE: provider adapter / host model
4. REVIEW: result-review + failure-analysis if necessary

Logical modularity does not require eight separate inference calls.

## Integration modes

### Host-model mode
A capable AI host performs vision/generation itself while PoseFix supplies skills/contracts/workflow.

### Engine-provider mode
PoseFix calls a configured adapter such as OpenAI, Gemini, FLUX, or ComfyUI.

## Future surfaces
- MCP server
- plugin package
- CLI/Python package
- optional reference UI
