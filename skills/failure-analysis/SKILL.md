# Failure Analysis Skill

## Purpose
Explain why a generated attempt failed and recommend the cheapest safe recovery.

## Examples
- Identity drift -> tighten identity preservation / reduce edit strength.
- Bad hands -> preserve original hand geometry.
- Background drift -> reduce edited region / tighten background preservation.
- Pose under-applied -> strengthen pose adherence without broadening reconstruction.

## Boundary
The skill recommends recovery. The engine owns retry count and execution state.
