# PoseFix contracts

These schemas are intentionally provider-neutral. They define hand-off points between skills, deterministic engine code, and rendering adapters.

- `pose_analysis.v1.json`: observed state from image analysis.
- `composite_plan.v1.json`: deterministic primary/secondary preset plan.
- `pose_target.v1.json`: intended corrected body state.
- `generation_spec.v1.json`: provider-neutral image edit job.
- `generation_result.v1.json`: normalized provider result.
- `result_review.v1.json`: reviewer decision and scores.
