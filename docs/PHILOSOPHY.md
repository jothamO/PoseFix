# Design philosophy

PoseFix starts from a different question than a general image editor:

**What is already working in this photo, and what is the smallest pose change needed?**

That leads to four project rules:

1. Preserve before changing.
2. Diagnose before generating.
3. Prefer the lowest-risk correction that solves the problem.
4. Review the output against both the original image and the intended pose target.

The project is provider-agnostic on purpose. Pose knowledge belongs in skills and presets, deterministic decisions belong in the engine, and vendor details belong in adapters.
