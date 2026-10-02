from posefix.experimental.group import (
    build_group_generation_spec,
    build_group_target,
    build_progressive_steps,
    choose_generation_strategy,
    summarize_experiment_result,
)


def _pair_target(*, contact=False, locked_first=False, occlusions=0, operations=None):
    relationships = []
    if contact:
        relationships.append(
            {"a": "p1", "b": "p2", "interaction": "shoulder_contact"}
        )
    analysis = {
        "people_count": 2,
        "people": [
            {"person_id": "p1", "locked": locked_first},
            {"person_id": "p2", "locked": False},
        ],
        "relationships": relationships,
        "occlusion_edges": [
            {"front": "p1", "behind": "p2", "region": f"r{i}"}
            for i in range(occlusions)
        ],
        "horizontal_space": "high",
        "occlusion_complexity": "medium" if occlusions else "low",
        "depth_cues": "moderate",
    }
    return build_group_target(
        analysis,
        "side_by_side",
        operations=operations or [],
    )


def test_simple_pair_prefers_whole_group():
    target = _pair_target()

    assert choose_generation_strategy(target) == "whole_group"


def test_contact_pair_prefers_progressive_constrained():
    target = _pair_target(contact=True)

    assert choose_generation_strategy(target) == "progressive_constrained"


def test_high_reconstruction_debt_prefers_progressive_constrained():
    target = _pair_target(
        operations=["reveal_hidden_limb"],
    )

    assert choose_generation_strategy(target) == "progressive_constrained"


def test_generation_spec_locks_two_person_authority_and_budget():
    target = _pair_target()
    spec = build_group_generation_spec(
        source_image_id="pair_001",
        target=target,
        strategy="whole_group",
    )

    assert spec["schema_version"] == "group_generation_spec.v0"
    assert spec["generation_constraints"]["person_count"] == 2
    assert spec["generation_constraints"]["identity_slots_must_persist"] is True
    assert spec["authority"]["template_or_reference"] == ["geometry_only"]
    assert spec["budget"]["max_generation_calls"] == 2
    assert spec["budget"]["targeted_retries"] == 1


def test_progressive_steps_respect_locked_person():
    target = _pair_target(locked_first=True)
    spec = build_group_generation_spec(
        source_image_id="pair_002",
        target=target,
        strategy="progressive_constrained",
    )

    steps = build_progressive_steps(spec)

    edit_steps = [step for step in steps if "edit_person_id" in step]
    assert len(edit_steps) == 1
    assert edit_steps[0]["edit_person_id"] == "p2"
    assert steps[-1]["operation"] == "group_reconciliation"


def test_experiment_summary_keeps_cost_and_failure_evidence():
    result = summarize_experiment_result(
        strategy="whole_group",
        generation_calls=2,
        review_calls=2,
        first_pass=False,
        retry_used=True,
        violations=["GROUP_CONTACT_FAILURE", "GROUP_CONTACT_FAILURE"],
        validated=False,
        provider_cost=0.42,
    )

    assert result["validated"] is False
    assert result["provider_cost"] == 0.42
    assert result["failure_classes"] == ["GROUP_CONTACT_FAILURE"]
