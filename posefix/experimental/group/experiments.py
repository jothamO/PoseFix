from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

GenerationStrategy = Literal["whole_group", "progressive_constrained"]


@dataclass(frozen=True)
class GXExperimentBudget:
    max_generation_calls: int = 2
    max_review_calls: int = 2
    targeted_retries: int = 1


def choose_generation_strategy(
    target: dict[str, Any],
    *,
    preferred: GenerationStrategy | None = None,
) -> GenerationStrategy:
    """Choose an experimental two-person generation strategy.

    GX-D1 keeps strategy selection deterministic and inspectable. High-contact
    or occlusion-heavy targets prefer progressive constrained editing; simpler
    pairs prefer one whole-group edit.
    """
    if preferred:
        return preferred

    graph = target.get("group_pose_graph", {})
    relationships = graph.get("relationships", [])
    occlusions = graph.get("occlusion_edges", [])
    debt = float(graph.get("reconstruction_debt", {}).get("total", 0.0))

    has_contact = any(
        edge.get("interaction")
        not in {None, "none", "preserve", "proximity"}
        for edge in relationships
    )
    if has_contact or len(occlusions) > 1 or debt >= 0.30:
        return "progressive_constrained"
    return "whole_group"


def build_group_generation_spec(
    *,
    source_image_id: str,
    target: dict[str, Any],
    strategy: GenerationStrategy,
) -> dict[str, Any]:
    people = target.get("group_pose_graph", {}).get("people", [])
    if len(people) != 2:
        raise ValueError("GX-D1 supports exactly two people")

    return {
        "schema_version": "group_generation_spec.v0",
        "experiment": {
            "milestone": "GX-D1",
            "status": "experimental",
            "strategy": strategy,
        },
        "source": {
            "image_id": source_image_id,
            "role": "authoritative_source",
        },
        "target": target,
        "authority": {
            "original": [
                "identity",
                "face",
                "body_appearance",
                "clothing",
                "accessories",
                "background",
                "lighting",
                "camera_world",
            ],
            "template_or_reference": ["geometry_only"],
        },
        "generation_constraints": {
            "person_count": 2,
            "identity_slots_must_persist": True,
            "appearance_migration_forbidden": True,
            "new_people_forbidden": True,
            "missing_people_forbidden": True,
            "unapproved_intimate_contact_forbidden": True,
            "invent_scene_object_forbidden": True,
        },
        "budget": {
            "max_generation_calls": 2,
            "max_review_calls": 2,
            "targeted_retries": 1,
        },
    }


def build_progressive_steps(spec: dict[str, Any]) -> list[dict[str, Any]]:
    if spec["experiment"]["strategy"] != "progressive_constrained":
        return []

    people = spec["target"]["group_pose_graph"]["people"]
    unlocked = [person for person in people if not person.get("locked")]
    if not unlocked:
        return []

    steps = []
    for index, person in enumerate(unlocked, start=1):
        steps.append(
            {
                "step": index,
                "edit_person_id": person["person_id"],
                "freeze_other_people": True,
                "preserve_scene": True,
                "require_intermediate_review": True,
            }
        )
    steps.append(
        {
            "step": len(steps) + 1,
            "operation": "group_reconciliation",
            "freeze_identity_slots": True,
            "preserve_scene": True,
        }
    )
    return steps


def summarize_experiment_result(
    *,
    strategy: GenerationStrategy,
    generation_calls: int,
    review_calls: int,
    first_pass: bool,
    retry_used: bool,
    violations: list[str],
    validated: bool,
    provider_cost: float | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "group_experiment_result.v0",
        "strategy": strategy,
        "generation_calls": generation_calls,
        "review_calls": review_calls,
        "first_pass_success": first_pass,
        "targeted_retry_used": retry_used,
        "violations": violations,
        "validated": validated,
        "provider_cost": provider_cost,
        "failure_classes": sorted(set(violations)),
    }
