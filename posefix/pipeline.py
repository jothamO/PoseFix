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


def _review_candidate(
    *,
    source_image_path: str,
    target: dict[str, Any],
    spec: dict[str, Any],
    candidate: dict[str, Any],
    review_adapter: Any,
) -> dict[str, Any] | None:
    generated_path = candidate.get("image_ref")
    if not generated_path or not Path(generated_path).exists():
        return None

    review = review_adapter.review(
        source_image_path=source_image_path,
        generated_image_path=generated_path,
        pose_target=target,
        generation_spec=spec,
    )
    validate_contract(review)
    return review


def _is_distinct_from_accepted(
    *,
    review_adapter: Any,
    accepted_outputs: list[dict[str, Any]],
    candidate_path: str,
    intensity: str,
) -> tuple[bool, float | None]:
    distinctness_checker = getattr(review_adapter, "compare_variants", None)
    if not distinctness_checker or not accepted_outputs:
        return True, None

    minimum_score = 1.0
    for accepted_output in accepted_outputs:
        comparison = distinctness_checker(
            accepted_image_path=accepted_output["image_ref"],
            candidate_image_path=candidate_path,
            intensity=intensity,
        )
        score = float(comparison.get("distinctness_score", 0.0))
        minimum_score = min(minimum_score, score)
        if not bool(comparison.get("materially_distinct", False)) or score < 0.80:
            return False, score
    return True, minimum_score


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
    requested_count = len(variants)
    accepted_outputs: list[dict[str, Any]] = []
    accepted_reviews: list[dict[str, Any]] = []
    attempt_log: list[dict[str, Any]] = []
    provider: dict[str, Any] = {}
    request: dict[str, Any] = {}
    warnings: list[Any] = []
    errors: list[Any] = []
    intensity = spec["selected_preset"]["intensity"]

    # Cost-bounded policy:
    # 1) generate the requested choices once as a batch,
    # 2) keep only candidates that pass review and distinctness,
    # 3) give each failed slot exactly one targeted replacement attempt.
    initial_generation = image_adapter.generate(
        source_image_path=source_image_path,
        generation_spec=spec,
        output_dir=str(Path(output_dir) / "initial"),
    )
    validate_contract(initial_generation)

    provider = initial_generation.get("provider", {})
    request = initial_generation.get("request", {})
    warnings.extend(initial_generation.get("warnings", []))
    errors.extend(initial_generation.get("errors", []))

    initial_outputs = initial_generation.get("outputs", [])
    failed_slots: list[tuple[int, dict[str, Any], dict[str, Any] | None]] = []

    for slot_index, variant in enumerate(variants):
        slot_id = variant.get("variant_id", f"option_{slot_index + 1}")
        candidate = initial_outputs[slot_index] if slot_index < len(initial_outputs) else None
        if not candidate:
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 1,
                    "decision": "RETRY",
                    "reason": "no_candidate_output",
                }
            )
            failed_slots.append(
                (
                    slot_index,
                    variant,
                    {
                        "decision": "RETRY",
                        "retry_recommendation": {"strategy": "retry_provider_output"},
                    },
                )
            )
            continue

        review = _review_candidate(
            source_image_path=source_image_path,
            target=target,
            spec=spec,
            candidate=candidate,
            review_adapter=review_adapter,
        )
        if review is None:
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 1,
                    "decision": "RETRY",
                    "reason": "missing_candidate_file",
                }
            )
            failed_slots.append(
                (
                    slot_index,
                    variant,
                    {
                        "decision": "RETRY",
                        "retry_recommendation": {"strategy": "retry_provider_output"},
                    },
                )
            )
            continue

        decision = review.get("decision")
        attempt_log.append(
            {
                "variant_id": slot_id,
                "attempt": 1,
                "decision": decision,
                "overall_score": review.get("overall_score"),
                "retry_recommendation": review.get("retry_recommendation"),
            }
        )

        if decision == "PASS":
            generated_path = candidate["image_ref"]
            distinct, score = _is_distinct_from_accepted(
                review_adapter=review_adapter,
                accepted_outputs=accepted_outputs,
                candidate_path=generated_path,
                intensity=intensity,
            )
            if distinct:
                accepted = dict(candidate)
                accepted["output_id"] = f"out_{slot_index + 1:03d}"
                accepted["variant_id"] = slot_id
                metadata = dict(accepted.get("generation_metadata", {}))
                metadata["attempt"] = 1
                accepted["generation_metadata"] = metadata
                accepted_outputs.append(accepted)
                accepted_reviews.append(review)
                continue

            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 1,
                    "decision": "RETRY",
                    "reason": "insufficient_variant_distinctness",
                    "distinctness_score": score,
                }
            )
            review = {
                "decision": "RETRY",
                "retry_recommendation": {"strategy": "diversify_pose_solution"},
            }

        failed_slots.append((slot_index, variant, review))

    # One targeted retry per failed slot. No final retry.
    for slot_index, variant, previous_review in failed_slots:
        slot_id = variant.get("variant_id", f"option_{slot_index + 1}")
        retry_spec = _retry_spec(
            spec,
            variant=variant,
            attempt=2,
            previous_review=previous_review,
        )
        retry_generation = image_adapter.generate(
            source_image_path=source_image_path,
            generation_spec=retry_spec,
            output_dir=str(Path(output_dir) / slot_id / "retry"),
        )
        validate_contract(retry_generation)

        provider = retry_generation.get("provider", provider)
        warnings.extend(retry_generation.get("warnings", []))
        errors.extend(retry_generation.get("errors", []))
        candidates = retry_generation.get("outputs", [])
        if not candidates:
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 2,
                    "decision": "UNFILLED",
                    "reason": "targeted_retry_failed",
                }
            )
            continue

        candidate = candidates[0]
        review = _review_candidate(
            source_image_path=source_image_path,
            target=target,
            spec=retry_spec,
            candidate=candidate,
            review_adapter=review_adapter,
        )
        if review is None:
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 2,
                    "decision": "UNFILLED",
                    "reason": "targeted_retry_missing_file",
                }
            )
            continue

        decision = review.get("decision")
        attempt_log.append(
            {
                "variant_id": slot_id,
                "attempt": 2,
                "decision": decision,
                "overall_score": review.get("overall_score"),
                "retry_recommendation": review.get("retry_recommendation"),
            }
        )
        if decision != "PASS":
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 2,
                    "decision": "UNFILLED",
                    "reason": "targeted_retry_did_not_pass",
                }
            )
            continue

        generated_path = candidate["image_ref"]
        distinct, score = _is_distinct_from_accepted(
            review_adapter=review_adapter,
            accepted_outputs=accepted_outputs,
            candidate_path=generated_path,
            intensity=intensity,
        )
        if not distinct:
            attempt_log.append(
                {
                    "variant_id": slot_id,
                    "attempt": 2,
                    "decision": "UNFILLED",
                    "reason": "targeted_retry_not_distinct",
                    "distinctness_score": score,
                }
            )
            continue

        accepted = dict(candidate)
        accepted["output_id"] = f"out_{slot_index + 1:03d}"
        accepted["variant_id"] = slot_id
        metadata = dict(accepted.get("generation_metadata", {}))
        metadata["attempt"] = 2
        accepted["generation_metadata"] = metadata
        accepted_outputs.append(accepted)
        accepted_reviews.append(review)

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
            "generation_budget": requested_count + len(failed_slots),
            "generation_budget_policy": "initial_batch_plus_one_targeted_retry_per_failed_slot",
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
