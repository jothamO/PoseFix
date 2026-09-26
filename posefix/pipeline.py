from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .engine import build_generation_spec, build_pose_target, choose_plan
from .registry import load_presets, preset_map
from .validation import validate_contract


def analyze_and_plan(
    *,
    source_image_path: str,
    vision_adapter: Any,
    intensity: str = "natural",
) -> dict[str, Any]:
    analysis = vision_adapter.analyze(
        source_image_path=source_image_path
    )
    validate_contract(analysis)

    presets = load_presets()
    plan = choose_plan(analysis, presets, intensity=intensity)
    validate_contract(plan)

    if plan.get("selection_status") != "selected":
        return {
            "analysis": analysis,
            "plan": plan,
            "target": None,
            "generation_spec": None,
        }

    target = build_pose_target(
        analysis,
        plan,
        preset_map(),
    )
    validate_contract(target)

    spec = build_generation_spec(target)
    validate_contract(spec)

    return {
        "analysis": analysis,
        "plan": plan,
        "target": target,
        "generation_spec": spec,
    }


def _retry_spec(
    spec: dict[str, Any],
    *,
    variant: dict[str, Any],
    attempt: int,
    previous_review: dict[str, Any] | None,
) -> dict[str, Any]:
    retry_spec = copy.deepcopy(spec)
    retry_spec["task"]["output_count"] = 1
    retry_spec["variation_plan"] = [copy.deepcopy(variant)]
    retry_spec["variation_plan"][0]["attempt"] = attempt

    if previous_review:
        strategy = (previous_review.get("retry_recommendation") or {}).get("strategy")
        if strategy:
            retry_spec["variation_plan"][0]["retry_strategy"] = strategy
            retry_spec["transform"]["summary"] += (
                f" Retry this option using strategy={strategy}. "
                "The previous candidate is not user-visible and must be replaced."
            )
        if strategy == "restore_requested_intensity_mode":
            intensity = retry_spec["selected_preset"]["intensity"]
            retry_spec["transform"]["summary"] += (
                f" The replacement must unmistakably read as {intensity}, not as a "
                "weaker or stronger neighboring mode."
            )

    return retry_spec


def generate_and_review(
    *,
    source_image_path: str,
    planned: dict[str, Any],
    image_adapter: Any,
    review_adapter: Any | None,
    output_dir: str,
) -> dict[str, Any]:
    spec = planned.get("generation_spec")
    target = planned.get("target")
    if not spec or not target:
        return {
            **planned,
            "generation": None,
            "reviews": [],
            "attempt_log": [],
        }

    # Without a reviewer there is no safe output gate, so preserve the legacy
    # single generation path for low-level/debug use only.
    if review_adapter is None:
        generation = image_adapter.generate(
            source_image_path=source_image_path,
            generation_spec=spec,
            output_dir=output_dir,
        )
        validate_contract(generation)
        return {
            **planned,
            "generation": generation,
            "reviews": [],
            "attempt_log": [],
        }

    variants = spec.get("variation_plan", [])
    max_attempts = int(spec.get("retry_policy", {}).get("max_attempts", 4))
    accepted_outputs: list[dict[str, Any]] = []
    accepted_reviews: list[dict[str, Any]] = []
    attempt_log: list[dict[str, Any]] = []
    provider: dict[str, Any] = {}
    request: dict[str, Any] = {}
    warnings: list[Any] = []
    errors: list[Any] = []

    for slot_index, variant in enumerate(variants):
        previous_review: dict[str, Any] | None = None
        accepted = False
        slot_id = variant.get("variant_id", f"option_{slot_index + 1}")

        for attempt in range(1, max_attempts + 1):
            attempt_spec = _retry_spec(
                spec,
                variant=variant,
                attempt=attempt,
                previous_review=previous_review,
            )
            attempt_dir = str(Path(output_dir) / slot_id / f"attempt_{attempt}")
            generation = image_adapter.generate(
                source_image_path=source_image_path,
                generation_spec=attempt_spec,
                output_dir=attempt_dir,
            )
            validate_contract(generation)

            provider = generation.get("provider", provider)
            request = generation.get("request", request)
            warnings.extend(generation.get("warnings", []))
            errors.extend(generation.get("errors", []))

            candidates = generation.get("outputs", [])
            if not candidates:
                attempt_log.append(
                    {
                        "variant_id": slot_id,
                        "attempt": attempt,
                        "decision": "RETRY",
                        "reason": "no_candidate_output",
                    }
                )
                previous_review = {
                    "decision": "RETRY",
                    "retry_recommendation": {"strategy": "retry_provider_output"},
                }
                continue

            candidate = candidates[0]
            generated_path = candidate.get("image_ref")
            if not generated_path or not Path(generated_path).exists():
                attempt_log.append(
                    {
                        "variant_id": slot_id,
                        "attempt": attempt,
                        "decision": "RETRY",
                        "reason": "missing_candidate_file",
                    }
                )
                previous_review = {
                    "decision": "RETRY",
                    "retry_recommendation": {"strategy": "retry_provider_output"},
                }
                continue

            review = review_adapter.review(
                source_image_path=source_image_path,
                generated_image_path=generated_path,
                pose_target=target,
                generation_spec=attempt_spec,
            )
            validate_contract(review)
            decision = review.get("decision")

            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": attempt,
                    "decision": decision,
                    "overall_score": review.get("overall_score"),
                    "retry_recommendation": review.get("retry_recommendation"),
                }
            )

            if decision == "PASS":
                candidate = dict(candidate)
                candidate["output_id"] = f"out_{slot_index + 1:03d}"
                candidate["variant_id"] = slot_id
                metadata = dict(candidate.get("generation_metadata", {}))
                metadata["attempt"] = attempt
                candidate["generation_metadata"] = metadata
                accepted_outputs.append(candidate)
                accepted_reviews.append(review)
                accepted = True
                break

            previous_review = review

        if not accepted:
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": max_attempts,
                    "decision": "UNFILLED",
                    "reason": "retry_budget_exhausted",
                }
            )

    requested_count = len(variants)
    validated_count = len(accepted_outputs)
    if validated_count == requested_count:
        generation_status = "success"
    elif validated_count:
        generation_status = "partial_success"
    else:
        generation_status = "failed"

    generation = {
        "schema_version": "generation_result.v1",
        "generation_status": generation_status,
        "provider": provider,
        "request": {
            **request,
            "requested_variant_count": requested_count,
            "validated_variant_count": validated_count,
        },
        "outputs": accepted_outputs,
        "warnings": warnings,
        "errors": errors,
    }
    validate_contract(generation)

    return {
        **planned,
        "generation": generation,
        "reviews": accepted_reviews,
        "attempt_log": attempt_log,
    }
