from __future__ import annotations

from typing import Any

from .intensity import get_intensity_policy, scale_mechanic_strength


def build_pose_target(
    analysis: dict[str, Any],
    plan: dict[str, Any],
    presets_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if plan.get("selection_status") != "selected":
        return {
            "schema_version": "pose_target.v1",
            "target_status": "preserve_original",
            "selected_preset": None,
            "pose_target": {},
        }

    intensity = plan.get("intensity", "natural")
    policy = get_intensity_policy(intensity)
    mechanics: dict[str, dict[str, Any]] = {}
    for component in plan["components"]:
        preset = presets_by_id[component["preset_id"]]
        weight = float(component["weight"])

        for name, rule in preset.get("mechanics", {}).items():
            candidate = dict(rule)
            if isinstance(candidate.get("strength"), (int, float)):
                candidate["strength"] = scale_mechanic_strength(
                    intensity,
                    name,
                    float(candidate["strength"]) * weight,
                )

            existing = mechanics.get(name)
            if existing is None:
                mechanics[name] = candidate
                continue

            candidate_strength = candidate.get("strength")
            existing_strength = existing.get("strength")
            if (
                isinstance(candidate_strength, (int, float))
                and isinstance(existing_strength, (int, float))
                and candidate_strength > existing_strength
            ):
                mechanics[name] = candidate

    primary = plan["components"][0]["preset_id"]
    return {
        "schema_version": "pose_target.v1",
        "source_analysis_version": analysis["schema_version"],
        "target_status": "ready",
        "selected_preset": {
            "preset_id": primary,
            "label": plan.get("label", primary),
            "intensity": intensity,
            "selection_score": plan["ranked_candidates"][0]["score"],
        },
        "preservation": {
            item: "strict"
            for item in analysis.get("edit_plan", {}).get("preserve", [])
        },
        "pose_target": mechanics,
        "forbidden_changes": analysis.get("edit_plan", {}).get("avoid", []),
        "intensity_policy": {
            "mode": intensity,
            "mechanic_budget": policy.mechanic_budget,
            "change_magnitude": {
                "minimum": policy.change_magnitude[0],
                "maximum": policy.change_magnitude[1],
            },
            "pose_adherence_threshold": policy.pose_adherence_threshold,
            "reconstruction_tolerance": policy.reconstruction_tolerance,
            "status": policy.status,
        },
        "edit_budget": {
            "maximum_pose_change": policy.maximum_pose_change,
            "background_reconstruction_allowance": "minimal",
            "clothing_reconstruction_allowance": "minimal",
            "limb_reconstruction_allowance": policy.limb_reconstruction_allowance,
        },
        "fallback": {
            "if_target_not_feasible": "reduce_intensity",
            "fallback_intensity": (
                "enhanced" if intensity == "bold" else "natural"
            ),
            "if_still_not_feasible": "preserve_original_pose",
        },
    }


def build_generation_spec(target: dict[str, Any]) -> dict[str, Any]:
    preset = target.get("selected_preset")
    if target.get("target_status") != "ready" or not preset:
        raise ValueError("Pose target is not ready for generation")

    mechanics = []
    for name, rule in target.get("pose_target", {}).items():
        item = {
            "mechanic": name,
            "action": rule.get("action", "adjust"),
        }
        if "strength" in rule:
            item["strength"] = rule["strength"]
        mechanics.append(item)

    return {
        "schema_version": "generation_spec.v1",
        "source": {
            "image_id": "input_001",
            "role": "authoritative_source",
            "required": True,
        },
        "task": {
            "type": "pose_correction",
            "mode": "image_edit",
            "output_count": 1,
            "variation_policy": "controlled",
        },
        "selected_preset": {
            "preset_id": preset["preset_id"],
            "intensity": preset["intensity"],
        },
        "pose_target_ref": {
            "schema_version": "pose_target.v1",
            "target_id": "target_001",
        },
        "preservation_hierarchy": list(target.get("preservation", {}).keys()),
        "transform": {
            "summary": (
                (
                    "Apply the minimum necessary correction "
                    if preset["intensity"] == "natural"
                    else "Apply a clearly visible pose improvement "
                    if preset["intensity"] == "enhanced"
                    else "Apply a substantial pose transformation "
                )
                + f"for {preset['label']}, while preserving all protected details."
            ),
            "mechanics": mechanics,
        },
        "protected_regions": [
            {"region": "face", "policy": "strict_preserve"},
            {"region": "hair", "policy": "strict_preserve"},
            {
                "region": "hands",
                "policy": "preserve_function_and_appearance",
            },
            {
                "region": "clothing",
                "policy": "preserve_design_color_pattern_and_fit",
            },
            {"region": "accessories", "policy": "strict_preserve"},
        ],
        "mutable_regions": [],
        "scene_constraints": {
            "background": "preserve",
            "lighting": "preserve",
            "shadows": "preserve_and_reconcile",
            "ground_contact": "strict",
            "support_object_contact": "preserve",
            "occlusion_order": "preserve",
            "camera_position": "preserve",
            "camera_height": "preserve",
            "lens_character": "preserve",
            "crop": "preserve",
        },
        "negative_constraints": list(target.get("forbidden_changes", [])),
        "edit_budget": target["edit_budget"],
        "regional_guidance": {
            "mask_strategy": "auto_if_supported",
            "preferred_edit_region": "subject_body_excluding_face_when_possible",
            "protect_face": True,
            "protect_background": True,
        },
        "control_hints": {
            "pose_control": {"preferred": True, "required": False},
            "identity_reference": {"preferred": True, "required": False},
            "masking": {"preferred": True, "required": False},
            "seed_control": {"preferred": False, "required": False},
        },
        "output_requirements": {
            "preserve_resolution": True,
            "preserve_aspect_ratio": True,
            "minimum_quality": "production",
            "return_metadata": True,
        },
        "variation_plan": [
            {"variant_id": preset["intensity"], "intensity_multiplier": 1.0}
        ],
        "retry_policy": {
            "max_attempts": 2,
            "on_identity_drift": "reduce_edit_strength",
            "on_background_drift": "tighten_preservation",
            "on_anatomy_failure": "retry_with_stricter_pose_constraints",
            "on_hand_failure": "preserve_original_hand_geometry",
            "on_pose_failure": "retry_under_applied_mechanics_then_fallback",
        },
        "review_requirements": {
            "must_check": [
                "identity_retention",
                "pose_target_adherence",
                "anatomical_plausibility",
                "hand_quality",
                "clothing_retention",
                "background_retention",
                "lighting_consistency",
                "ground_contact",
            ]
        },
    }
