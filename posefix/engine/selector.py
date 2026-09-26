from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .intensity import get_intensity_policy

RISK_PENALTY = {
    "low": 0.0,
    "medium": 0.08,
    "high": 0.18,
}


ISSUE_SPECIALISTS = {
    "centered_weight": {"soft_weight_shift"},
    "locked_knees": {"soft_weight_shift"},
    "over_symmetric_legs": {"soft_weight_shift"},
    "square_hips": {"turned_slightly"},
    "square_shoulders": {"turned_slightly"},
    "rounded_shoulders": {"open_shoulders", "straighten_up"},
    "arms_pressed_to_torso": {"open_shoulders"},
    "slightly_closed_arms": {"open_shoulders"},
    "slouched_torso": {"straighten_up", "professional_presence"},
    "rigid_torso": {"relaxed_upright"},
    "compressed_neck": {"straighten_up"},
    "chin_too_high": {"chin_gaze_fix"},
    "chin_too_low": {"chin_gaze_fix"},
    "chin_retracted": {"chin_gaze_fix"},
    "chin_overprojected": {"chin_gaze_fix"},
    "accidental_gaze": {"chin_gaze_fix"},
    "unclear_gaze": {"chin_gaze_fix", "professional_presence"},
    "unclear_hand_purpose": {"one_hand_purpose"},
    "awkward_wrist": {"one_hand_purpose"},
    "excessive_symmetry": {
        "soft_weight_shift",
        "turned_slightly",
        "casual_confidence",
    },
}


@dataclass(frozen=True)
class ScoredPreset:
    preset_id: str
    score: float
    reasons: tuple[str, ...]


def _issue_contribution(
    issue: dict[str, Any],
    preset: dict[str, Any],
) -> float:
    if issue["id"] not in preset.get("issue_matches", []):
        return 0.0
    return float(issue.get("severity", 0)) * float(
        issue.get("confidence", 0)
    )


def _issue_fit(
    issues: list[dict[str, Any]],
    preset: dict[str, Any],
) -> tuple[float, list[str], float]:
    contributions = [
        _issue_contribution(issue, preset)
        for issue in issues
    ]
    matched = [
        issues[index]["id"]
        for index, value in enumerate(contributions)
        if value > 0
    ]
    matched_values = sorted(
        (value for value in contributions if value > 0),
        reverse=True,
    )
    if not matched_values:
        return 0.0, [], 0.0

    strongest = matched_values[0]
    supporting = matched_values[1] if len(matched_values) > 1 else 0.0
    coverage_score = 0.65 * strongest + 0.35 * supporting

    specialist_weight = 0.0
    for issue, contribution in zip(issues, contributions, strict=True):
        if contribution <= 0:
            continue
        specialists = ISSUE_SPECIALISTS.get(issue["id"], set())
        if preset["preset_id"] in specialists:
            specialist_weight = max(specialist_weight, contribution)

    return coverage_score, matched, specialist_weight


def _visibility_score(
    analysis: dict[str, Any],
    preset: dict[str, Any],
) -> float:
    visibility = analysis["subject"]["visibility"]

    def visible(region: str) -> bool:
        accepted = {"fully_visible", "partially_visible"}
        if region == "at_least_one_knee":
            return visibility.get("knees") in accepted
        if region == "at_least_one_hand":
            return visibility.get("hands") in accepted
        if region in {"at_least_one_elbow", "upper_arms"}:
            return visibility.get("elbows") in accepted
        return visibility.get(region) in accepted

    return (
        1.0
        if all(
            visible(region)
            for region in preset.get("required_visible_regions", [])
        )
        else 0.0
    )


def score_presets(
    analysis: dict[str, Any],
    presets: list[dict[str, Any]],
) -> list[ScoredPreset]:
    issues = analysis["diagnosis"].get("issues", [])
    scored: list[ScoredPreset] = []

    for preset in presets:
        visibility = _visibility_score(analysis, preset)
        pose_type = analysis["subject"]["pose_type"]
        pose_score = (
            1.0
            if pose_type in preset.get("supported_pose_types", [])
            else 0.0
        )
        crop = analysis["image"]["crop"]
        crop_score = (
            1.0 if crop in preset.get("supported_crops", []) else 0.0
        )

        if 0.0 in {visibility, pose_score, crop_score}:
            continue

        issue_score, matched, specialist_weight = _issue_fit(
            issues,
            preset,
        )
        if issue_score == 0:
            continue

        scene_score = (
            1.0
            if analysis["subject"].get("support_context", "none") == "none"
            else 0.85
        )
        feasibility = {
            "high": 1.0,
            "medium": 0.7,
            "low": 0.35,
        }.get(
            analysis.get("feasibility", {}).get("overall", "medium"),
            0.7,
        )

        preservation = 0.9
        if preset["preset_id"] == "one_hand_purpose" and any(
            item.get("mechanic") == "hand_purpose"
            for item in analysis["diagnosis"].get("working_elements", [])
        ):
            preservation = 0.0

        specialist_bonus = 0.03 * specialist_weight

        score = (
            0.30 * issue_score
            + 0.20 * visibility
            + 0.15 * pose_score
            + 0.15 * scene_score
            + 0.10 * preservation
            + 0.10 * feasibility
            + specialist_bonus
            - RISK_PENALTY.get(preset.get("risk", "medium"), 0.08)
        )
        scored.append(
            ScoredPreset(
                preset["preset_id"],
                round(max(0.0, min(score, 1.0)), 4),
                tuple(matched),
            )
        )

    return sorted(
        scored,
        key=lambda item: (-item.score, item.preset_id),
    )


COMPATIBLE_SECONDARIES = {
    "straighten_up": {"open_shoulders", "chin_gaze_fix"},
    "relaxed_upright": {"open_shoulders", "chin_gaze_fix"},
    "open_shoulders": {"straighten_up", "soft_weight_shift"},
    "soft_weight_shift": {"turned_slightly", "open_shoulders"},
    "one_hand_purpose": {"relaxed_upright", "soft_weight_shift"},
    "turned_slightly": {"soft_weight_shift", "professional_presence"},
    "casual_confidence": {"chin_gaze_fix"},
    "professional_presence": {"turned_slightly", "chin_gaze_fix"},
    "editorial_lite": {"chin_gaze_fix"},
}


def choose_plan(
    analysis: dict[str, Any],
    presets: list[dict[str, Any]],
    intensity: str = "natural",
) -> dict[str, Any]:
    issues = analysis["diagnosis"].get("issues", [])
    correction_signal = max(
        (
            float(issue.get("severity", 0))
            * float(issue.get("confidence", 0))
            for issue in issues
        ),
        default=0.0,
    )

    policy = get_intensity_policy(intensity)

    if correction_signal < policy.correction_signal_threshold:
        return {
            "schema_version": "composite_plan.v1",
            "selection_status": "no_strong_correction",
            "recommendation": "preserve_original",
            "reason": "already_good_pose",
            "correction_signal": round(correction_signal, 4),
            "intensity": intensity,
            "components": [],
            "ranked_candidates": [],
        }

    ranked = score_presets(analysis, presets)
    strong = [item for item in ranked if item.score >= 0.68]

    if not strong:
        return {
            "schema_version": "composite_plan.v1",
            "selection_status": "no_strong_correction",
            "recommendation": "preserve_original",
            "intensity": intensity,
            "components": [],
            "ranked_candidates": [
                item.__dict__ for item in ranked
            ],
        }

    primary = strong[0]
    unresolved = {
        issue["id"]
        for issue in analysis["diagnosis"].get("issues", [])
    } - set(primary.reasons)

    secondary = None
    for candidate in strong[1:]:
        compatible = candidate.preset_id in COMPATIBLE_SECONDARIES.get(
            primary.preset_id,
            set(),
        )
        resolves_remaining = bool(unresolved.intersection(candidate.reasons))
        if (
            compatible
            and candidate.score >= 0.70
            and resolves_remaining
        ):
            secondary = candidate
            break

    components = [
        {
            "preset_id": primary.preset_id,
            "role": "primary",
            "weight": 1.0,
        }
    ]
    label = next(
        preset["label"]
        for preset in presets
        if preset["preset_id"] == primary.preset_id
    )

    if secondary:
        components.append(
            {
                "preset_id": secondary.preset_id,
                "role": "secondary",
                "weight": policy.secondary_weight,
            }
        )
        label = (
            "Natural Upgrade"
            if intensity == "natural"
            else f"{intensity.title()} Upgrade"
        )

    return {
        "schema_version": "composite_plan.v1",
        "selection_status": "selected",
        "label": label,
        "intensity": intensity,
        "components": components,
        "ranked_candidates": [
            item.__dict__ for item in ranked
        ],
        "unresolved_issues": sorted(unresolved),
    }
