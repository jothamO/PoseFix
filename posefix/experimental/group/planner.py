from __future__ import annotations

from typing import Any

from .templates import GROUP_TEMPLATES


def _score_template(analysis: dict[str, Any], template: dict[str, Any]) -> tuple[float, list[str]]:
    people = int(analysis.get("people_count", 0))
    reasons: list[str] = []

    if not template["people_min"] <= people <= template["people_max"]:
        return 0.0, ["people_count_incompatible"]

    score = 1.0
    body_visibility = analysis.get("body_visibility", "unknown")
    horizontal_space = analysis.get("horizontal_space", "medium")
    occlusion = analysis.get("occlusion_complexity", "low")
    depth_cues = analysis.get("depth_cues", "moderate")

    if template["depth_layers"] >= 3 and depth_cues == "low":
        score -= 0.30
        reasons.append("insufficient_depth_cues")

    if template["formation"] in {"line", "center_wings"} and horizontal_space == "low":
        score -= 0.25
        reasons.append("limited_horizontal_space")

    if template["contact_density"] == "high" and occlusion == "high":
        score -= 0.25
        reasons.append("contact_occlusion_risk")

    if body_visibility == "upper_body" and template["formation"] == "layered_cluster":
        score -= 0.20
        reasons.append("limited_body_visibility")

    if analysis.get("support_object_dependency") and template["risk"] == "high":
        score -= 0.15
        reasons.append("support_object_reconstruction_risk")

    return max(0.0, round(score, 3)), reasons


def recommend_templates(analysis: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for template_id, template in GROUP_TEMPLATES.items():
        score, reasons = _score_template(analysis, template)
        if score <= 0:
            continue
        ranked.append(
            {
                "template_id": template_id,
                "label": template["label"],
                "compatibility_score": score,
                "reasons": reasons,
                "risk": template["risk"],
            }
        )
    ranked.sort(key=lambda item: (-item["compatibility_score"], item["risk"], item["template_id"]))
    return ranked[:limit]


def classify_compatibility(score: float) -> str:
    if score >= 0.80:
        return "compatible"
    if score >= 0.55:
        return "adaptable"
    if score > 0:
        return "high_risk"
    return "unsupported"


def map_reference_roles(
    source_people: list[dict[str, Any]],
    reference_slots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Greedy geometry-only mapping.

    GX-D0 deliberately avoids identity/appearance similarity. Mapping uses
    spatial and visibility compatibility so the reference cannot influence
    who a source person is.
    """
    remaining = reference_slots[:]
    assignments: list[dict[str, Any]] = []

    for person in sorted(source_people, key=lambda item: item.get("x", 0.5)):
        if not remaining:
            break

        person_x = float(person.get("x", 0.5))
        person_visibility = person.get("body_visibility")

        def cost(
            slot: dict[str, Any],
            *,
            bound_person_x: float = person_x,
            bound_person_visibility: Any = person_visibility,
        ) -> float:
            spatial = abs(bound_person_x - float(slot.get("x", 0.5)))
            visibility_penalty = 0.0
            required = slot.get("required_visibility")
            if required and required != bound_person_visibility:
                visibility_penalty = 0.25
            return spatial + visibility_penalty

        slot = min(remaining, key=cost)
        remaining.remove(slot)
        assignments.append(
            {
                "person_id": person["person_id"],
                "slot_id": slot["slot_id"],
                "mapping_basis": "geometry_only",
                "cost": round(cost(slot), 3),
            }
        )

    return assignments


RECONSTRUCTION_DEBT_WEIGHTS = {
    "small_posture_adjustment": 0.05,
    "small_spacing_adjustment": 0.08,
    "torso_rotation": 0.10,
    "hand_role_change": 0.12,
    "depth_order_change": 0.20,
    "reveal_hidden_limb": 0.35,
    "invent_scene_object": 1.00,
}


def estimate_reconstruction_debt(operations: list[str]) -> dict[str, Any]:
    total = 0.0
    forbidden: list[str] = []
    applied: list[dict[str, Any]] = []

    for operation in operations:
        weight = float(RECONSTRUCTION_DEBT_WEIGHTS.get(operation, 0.15))
        if operation == "invent_scene_object":
            forbidden.append(operation)
        total += weight
        applied.append({"operation": operation, "weight": weight})

    return {
        "total": round(total, 3),
        "operations": applied,
        "forbidden_operations": forbidden,
    }


def adapt_template(
    template_id: str,
    people: list[dict[str, Any]],
) -> dict[str, Any]:
    template = GROUP_TEMPLATES[template_id]
    count = len(people)
    if not template["people_min"] <= count <= template["people_max"]:
        return {
            "template_id": template_id,
            "status": "unsupported",
            "reason": "people_count_incompatible",
            "slots": [],
        }

    slots: list[dict[str, Any]] = []
    roles = template["slot_roles"]
    for index, person in enumerate(people):
        role = roles[index] if index < len(roles) else "optional"
        slots.append(
            {
                "slot_id": f"slot_{index + 1}",
                "person_id": person["person_id"],
                "role": role,
                "locked": bool(person.get("locked", False)),
                "requirement": "required" if index < template["people_min"] else "optional",
            }
        )

    return {
        "template_id": template_id,
        "status": "adapted",
        "formation": template["formation"],
        "slots": slots,
    }


def build_group_target(
    analysis: dict[str, Any],
    template_id: str,
    *,
    operations: list[str] | None = None,
    compatibility_score: float | None = None,
) -> dict[str, Any]:
    people = list(analysis.get("people", []))
    adaptation = adapt_template(template_id, people)
    if adaptation["status"] == "unsupported":
        return {
            "schema_version": "group_target.v0",
            "target_status": "unsupported",
            "compatibility": "unsupported",
            "group_pose_graph": {},
            "locked_people": [
                person["person_id"] for person in people if person.get("locked")
            ],
            "forbidden_changes": ["invent_scene_object", "identity_reassignment"],
        }

    if compatibility_score is None:
        template = GROUP_TEMPLATES[template_id]
        compatibility_score, _ = _score_template(analysis, template)

    compatibility = classify_compatibility(compatibility_score)
    if compatibility == "unsupported":
        status = "unsupported"
    elif compatibility == "compatible":
        status = "ready"
    else:
        status = "adapted"

    debt = estimate_reconstruction_debt(operations or [])
    if debt["forbidden_operations"]:
        status = "unsupported"
        compatibility = "unsupported"

    locked_people = [
        person["person_id"] for person in people if person.get("locked")
    ]

    person_nodes = []
    for slot in adaptation["slots"]:
        pose_policy = "preserve" if slot["locked"] else "adapt_to_template"
        person_nodes.append(
            {
                "person_id": slot["person_id"],
                "slot_id": slot["slot_id"],
                "role": slot["role"],
                "locked": slot["locked"],
                "pose": {"policy": pose_policy},
                "appearance_owner": slot["person_id"],
            }
        )

    relationships = [
        {
            "a": edge["a"],
            "b": edge["b"],
            "interaction": edge.get("interaction", "preserve"),
            "policy": "preserve_unless_template_requires_change",
        }
        for edge in analysis.get("relationships", [])
    ]
    occlusion_edges = [
        {
            "front": edge["front"],
            "behind": edge["behind"],
            "region": edge.get("region"),
            "policy": "preserve_or_explicitly_replan",
        }
        for edge in analysis.get("occlusion_edges", [])
    ]

    return {
        "schema_version": "group_target.v0",
        "target_status": status,
        "compatibility": compatibility,
        "group_pose_graph": {
            "schema_version": "group_pose_graph.v0",
            "people": person_nodes,
            "relationships": relationships,
            "composition": {
                "formation": adaptation["formation"],
                "template_id": template_id,
            },
            "occlusion_edges": occlusion_edges,
            "reconstruction_debt": debt,
        },
        "locked_people": locked_people,
        "forbidden_changes": [
            "invent_scene_object",
            "identity_reassignment",
            "appearance_cross_contamination",
            "unapproved_intimate_contact",
        ],
    }
