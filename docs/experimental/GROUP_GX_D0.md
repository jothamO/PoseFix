# GX-D0 — Group Representation & Experience

Status: **experimental**. This work does not change PoseFix V1 scope or public launch gates.

## Experimental invariant

> Every person remains themselves. Every relationship remains intentional. Every generated change must belong to a known person, pose, or composition constraint.

## Why GX-D0 exists

Group correction is not modeled as single-person PoseFix multiplied by N. GX-D0 exists to validate the representation and experience before any live multi-person generation work.

The system explicitly represents:
- stable person ownership
- per-person pose state
- group composition
- relationship/contact edges
- occlusion order
- reconstruction debt
- template compatibility
- optional pose-reference geometry

Prompt-only multi-person editing is not considered an acceptable architecture.

## Authority model

Four independent authorities are kept separate:

1. **Original image** — identity, face, body appearance, clothing, accessories, background, lighting, camera world.
2. **Group template** — abstract composition and interaction structure.
3. **Pose reference** — optional geometry/pose authority only.
4. **PoseFix intensity** — how far the engine may move from the source arrangement.

Reference images must never transfer identity, clothing, accessories, background, lighting, or scene identity.

## Experimental contracts

- `group_analysis.v0`
- `group_template.v0`
- `group_pose_graph.v0`
- `group_reference.v0`
- `group_target.v0`
- `group_result_review.v0`

These are intentionally unstable and are not part of the public API.

## Template grammar

GX-D0 starts with six structural programs:

- Side-by-Side
- V / Inward Pair
- Triangle
- Tight Cluster
- Center + Wings
- Layered Editorial

A template is a composition program, not a static reference image. Templates can define required/preferred/optional slots so a family may adapt across different people counts.

## Compatibility before generation

A source should be classified before any provider spend:

- `compatible`
- `adaptable`
- `high_risk`
- `unsupported`

Compatibility considers:
- people count
- body visibility
- available horizontal space
- depth cues
- occlusion burden
- contact burden
- support-object dependence
- reconstruction demand

## Reconstruction debt

Requested changes accumulate reconstruction debt. Low-debt operations include small posture or spacing adjustments. Revealing unseen anatomy, changing depth order, or creating support geometry carries much higher debt. Inventing new scene objects is forbidden rather than merely expensive.

The experimental planner should reject targets whose debt exceeds the allowed mode/source budget before generation.

## Identity ownership

Each source person receives a stable `person_id` that must survive analysis → target → generation → review.

Hard failures include:
- GROUP_PERSON_MISSING
- GROUP_EXTRA_PERSON
- GROUP_IDENTITY_SWAP
- GROUP_IDENTITY_BLEND
- GROUP_APPEARANCE_MIGRATION
- GROUP_CONTACT_FAILURE
- GROUP_OCCLUSION_FAILURE
- GROUP_FORMATION_FAILURE
- GROUP_VISIBILITY_FAILURE
- GROUP_SLOT_ASSIGNMENT_FAILURE
- GROUP_REFERENCE_LEAKAGE
- GROUP_REFERENCE_MAPPING_FAILURE
- GROUP_RECONSTRUCTION_EXCESS
- GROUP_TEMPLATE_INCOMPATIBLE
- GROUP_MODE_UNDER_APPLIED
- GROUP_MODE_OVER_APPLIED

No average group score may hide a ruined person.

## Review hierarchy

### Person level
- identity fidelity
- body-shape preservation
- clothing fidelity
- accessory fidelity
- anatomy
- hands
- pose adherence

### Relationship level
- contact ownership
- relative orientation
- spacing
- gaze
- occlusion order

### Group level
- formation adherence
- visibility
- composition
- scene preservation
- mode adherence

A result can pass only when all required levels pass.

## Reference mode

Reference mode follows:

```text
Original Group
      +
Reference Group
      ↓
independent analyses
      ↓
reference group graph
      ↓
geometry-only role mapping
      ↓
compatibility adaptation
      ↓
target group graph
```

Person mapping must use geometry/feasibility, not visual similarity.

## Experience prototypes

### Recommendation-first

```text
4 people detected

Try a better group pose

[ Close & Natural ]
[ Clean & Balanced ]
[ Editorial ]

Use a reference photo
```

The user chooses outcomes. The engine carries the structural complexity.

### Reference-first

```text
Original group
[image]

Pose reference
[upload]

PoseFix will borrow only the arrangement and pose.
Your people, clothes and setting stay yours.

[ Natural ] [ Enhanced ]
```

### Hidden automatic mapping

PoseFix should auto-map source people to target slots. Mapping controls stay hidden unless the user chooses **Adjust matching**.

### Lock person

A user may lock any person whose pose already works. The target composition must adapt around locked people.

## Experimental intensity

GX-D0 assumes only:
- **Group Natural**
- **Group Enhanced**

Group Bold is deliberately withheld until identity, contact, occlusion, and cost behavior are proven.

## People-count ladder

- GX0: 2 people — identity ownership, contact, overlap
- GX1: 3 people — true formation graph
- GX2: 4 people — permutation risk and template adaptation
- GX3: 5–6 people — layered composition and occlusion
- GX4: 7–10 people — scalable topology
- GX5: 10+ — separate future research problem

## GX-D0 exit gate

Do not begin live multi-person generation until synthetic/annotated fixtures can deterministically produce:

- ranked compatible templates
- explicit incompatibility reasons
- stable person IDs
- geometry-only role assignments
- locked-person handling
- target relationship graph
- target occlusion graph
- reconstruction-debt assessment
- expected review checks

Generation experiments begin only after these are coherent.

## Next milestone

**GX-D1 — 2-Person Generation Experiments**

Compare:
1. whole-group generation
2. progressive constrained editing

Track:
- first-pass success
- one targeted retry success
- identity leakage
- contact failures
- occlusion failures
- validated-result cost

No GX work blocks PoseFix's existing single-person pre-public-launch plan.


## GX-D0 hardening checkpoint

The deterministic planner now also proves the following before GX-D1:

- locked-person handling: a locked person receives `pose.policy=preserve`
- explicit template adaptation across supported people counts
- explicit target relationship graph preservation
- explicit target occlusion graph preservation
- reconstruction-debt accounting before provider spend
- scene-object invention is a forbidden operation, not a high-cost fallback
- appearance ownership remains bound to the original `person_id`

This checkpoint still performs no live multi-person generation.
