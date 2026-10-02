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
