from __future__ import annotations

from typing import Any

HARD_VIOLATIONS = {
    "age_change",
    "background_replacement",
    "body_reshape_detected",
    "broken_ground_contact",
    "extra_limb",
    "floating_subject",
    "identity_drift",
    "major_clothing_redesign",
    "missing_limb",
    "severe_hand_failure",
    "skin_tone_change",
}

THRESHOLDS = {
    "identity_retention": 0.90,
    "pose_target_adherence": 0.80,
    "anatomical_plausibility": 0.90,
    "hand_quality": 0.85,
    "clothing_retention": 0.90,
    "background_retention": 0.90,
    "lighting_consistency": 0.88,
    "ground_contact": 0.90,
    "body_shape_preservation": 0.95,
    "expression_preservation": 0.90,
}


def decide_review(
    checks: dict[str, float],
    violations: list[str],
) -> dict[str, Any]:
    hard = sorted(HARD_VIOLATIONS.intersection(violations))
    normalized = {
        key: {
            "score": float(value),
            "status": (
                "pass"
                if float(value) >= THRESHOLDS.get(key, 0.0)
                else "fail"
            ),
            "confidence": 1.0,
        }
        for key, value in checks.items()
    }

    if hard:
        decision = "REJECT"
    else:
        failed = [
            key
            for key, value in normalized.items()
            if value["status"] == "fail"
        ]
        retry_checks = (
            "identity_retention",
            "anatomical_plausibility",
            "hand_quality",
        )
        if not failed:
            decision = "PASS"
        elif any(key in failed for key in retry_checks):
            decision = "RETRY"
        else:
            decision = "FALLBACK"

    overall = sum(value["score"] for value in normalized.values()) / max(
        len(normalized),
        1,
    )
    return {
        "schema_version": "result_review.v1",
        "review_status": "complete",
        "decision": decision,
        "overall_score": round(overall, 4),
        "checks": normalized,
        "violations": violations,
        "retry_recommendation": (
            {"strategy": "reduce_pose_strength"}
            if decision == "RETRY"
            else None
        ),
        "fallback_recommendation": (
            {"target": "lower_intensity", "intensity": "subtle"}
            if decision == "FALLBACK"
            else None
        ),
    }
