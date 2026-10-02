# GX-D1 — Controlled 2-Person Generation Experiments

Status: **experimental**. GX-D1 is not part of PoseFix V1 and does not change the single-person public launch plan.

## Purpose

GX-D1 tests whether the GX-D0 representation can survive real two-person generation without collapsing identity, contact, occlusion, or cost.

The experiment compares two strategies:

1. **whole_group** — one provider edit receives the complete two-person target graph.
2. **progressive_constrained** — one person is edited at a time while the other person and scene are frozen, followed by group reconciliation.

No strategy is promoted in advance.

## Experimental constraints

GX-D1 supports exactly two people.

Hard rules:
- stable person IDs
- no missing or extra person
- no identity swap or blend
- no clothing/accessory migration
- no invented scene object
- no unapproved intimate contact
- source scene remains authoritative
- reference/template authority is geometry-only
- Group Bold remains disabled

## Cost bound

Each experimental case is bounded to:
- at most 2 generation calls
- at most 2 review calls
- at most 1 targeted retry

The purpose is to learn whether a strategy can succeed economically, not merely whether enough retries can eventually produce a good image.

## Metrics

Every run records:
- strategy
- first-pass success
- targeted-retry usage
- generation-call count
- review-call count
- provider cost where available
- validation result
- failure classes

Key comparison metric:

> validated group result cost per successful output

## Initial fixture families

GX-D1 should start with deliberately simple but diagnostic pair cases:

1. side-by-side, no contact
2. inward V, no contact
3. light shoulder contact
4. one person locked
5. mild occlusion
6. reference-derived pair geometry

Do not begin with hugs, intertwined hands, seated overlaps, or high-reconstruction poses.

## Exit criteria

GX-D1 is complete only when we have enough real runs to compare both strategies on:
- identity preservation
- person-slot stability
- contact correctness
- occlusion correctness
- scene preservation
- first-pass success
- retry success
- cost

The outcome may be:
- whole-group preferred
- progressive preferred
- hybrid routing
- or group generation not yet viable

Failure is an acceptable research result.
