# Pose Analysis Skill

## Purpose
Inspect one uploaded portrait and describe the observed pose without prescribing a final correction.

## Output
`pose_analysis.v1`

## Required reasoning
Classify crop, pose type, orientation, visibility, occlusion and support context; observe pose mechanics; record confidence separately from severity; record working elements; estimate feasibility conservatively.

## Forbidden behavior
Do not invent hidden anatomy, jump directly to provider prompts, treat low-confidence observations as certain, or evaluate attractiveness/body size.
