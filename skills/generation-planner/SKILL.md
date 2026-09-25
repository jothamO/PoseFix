# Generation Planner Skill

## Purpose
Translate the pose target into a provider-neutral image-edit job.

## Input
- source constraints
- `pose_target.v1`

## Output
- `generation_spec.v1`

## Rule
Describe intent, protected regions, mutable regions, edit budget, negative constraints, and review requirements. Never emit provider-specific CFG, denoise, node, or API parameters here.
