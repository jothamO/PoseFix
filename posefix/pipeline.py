from __future__ import annotations

from pathlib import Path
from typing import Any

from .engine import build_generation_spec, build_pose_target, choose_plan
from .registry import load_presets, preset_map
from .validation import validate_contract


def analyze_and_plan(
    *,
    source_image_path: str,
    vision_adapter: Any,
) -> dict[str, Any]:
    analysis = vision_adapter.analyze(
        source_image_path=source_image_path
    )
    validate_contract(analysis)

    presets = load_presets()
    plan = choose_plan(analysis, presets)
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
        }

    generation = image_adapter.generate(
        source_image_path=source_image_path,
        generation_spec=spec,
        output_dir=output_dir,
    )
    validate_contract(generation)

    reviews = []
    if (
        review_adapter
        and generation.get("generation_status")
        in {"success", "partial_success"}
    ):
        for output in generation.get("outputs", []):
            generated_path = output.get("image_ref")
            if not generated_path or not Path(generated_path).exists():
                continue

            review = review_adapter.review(
                source_image_path=source_image_path,
                generated_image_path=generated_path,
                pose_target=target,
                generation_spec=spec,
            )
            validate_contract(review)
            reviews.append(review)

    return {
        **planned,
        "generation": generation,
        "reviews": reviews,
    }
