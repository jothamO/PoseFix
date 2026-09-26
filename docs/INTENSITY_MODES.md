# PoseFix Intensity Modes

PoseFix supports three user-facing correction intensities.

## Natural
Status: **locked default**

Intent:
> Improve the pose with the smallest meaningful correction while preserving the original photographic moment.

Policy:
- strongest preserve-original gate
- secondary composite weight: 0.35
- pose adherence threshold: 0.80
- low reconstruction tolerance
- preservation standards remain strict

Natural is the existing validated PoseFix behavior and must not drift when Enhanced or Bold evolve.

## Enhanced
Status: **locked**

Intent:
> Apply a clearly visible re-pose within the existing photographic frame while preserving the subject, scene, identity, and composition.

Policy:
- lower intervention gate than Natural
- secondary composite weight: 0.50
- target budget: up to 4 major mechanics
- desired mechanic magnitude: 0.45-0.70
- pose adherence threshold: 0.86
- medium-low reconstruction tolerance
- may change the pose concept when that change can be achieved using anatomy already visible in the source frame
- may reassign hand purpose when the new pose requires it
- must preserve the existing crop/framing
- must not expand the crop to invent unseen anatomy merely to achieve a stronger pose
- must preserve identity, body shape, clothing, background, lighting, and camera relationship

Core rule:

> **Enhanced can re-pose. It should not re-compose the photograph.**

If the result preserves the photo but only achieves Natural-level correction, review should RETRY the under-applied mechanics. Tightening a retry must remove unsafe reconstruction without collapsing the requested intensity back toward Natural.

## Bold
Status: **locked**

Intent:
> Re-stage the subject with a stronger pose and controlled composition changes, while preserving the same person and photographic world.

Policy:
- permissive intervention gate
- secondary composite weight: 0.65
- target budget: up to 6 major mechanics
- desired mechanic magnitude: 0.70-1.00
- pose adherence threshold: 0.90
- medium reconstruction tolerance
- may substantially change the pose concept
- may freely reassign hand purpose when anatomically plausible
- may reinterpret support-object use
- may shift subject placement moderately
- may make a small subject-scale change
- may recompose framing within the existing image bounds
- must preserve the original image bounds
- must not fabricate a new full-body composition from a partial crop by default
- must preserve identity, body shape, clothing, scene, lighting, and camera-world continuity

Core rule:

> **Bold may re-stage and modestly re-compose, but it must not become a new photoshoot.**

Bold is harder to PASS, not easier: stronger transformation increases the pose-adherence requirement while preservation standards remain hard.

## Invariant

> **Intensity changes pose freedom, not preservation standards.**

Identity, body shape, skin tone, clothing design, background, lighting, and camera relationship remain protected across all three modes.

## Fallback ladder

```text
Bold
  -> retry under-applied mechanics
  -> Enhanced
  -> Natural
  -> preserve original

Enhanced
  -> retry under-applied mechanics
  -> Natural
  -> preserve original

Natural
  -> retry under-applied mechanics
  -> preserve original when correction benefit is too small
```

## Provider rule

Intensity is an engine policy, not a provider-specific prompt trick.

```text
Skills reason.
Engine governs.
Adapters translate.
```
