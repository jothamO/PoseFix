from pathlib import Path

from posefix.pipeline import generate_and_review


class FakeImageAdapter:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def generate(self, *, source_image_path, generation_spec, output_dir):
        self.calls += 1
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        path = out / "candidate.png"
        path.write_bytes(b"fake-image")
        return {
            "schema_version": "generation_result.v1",
            "generation_status": "success",
            "provider": {"name": "fake"},
            "request": {
                "generation_spec_version": "generation_spec.v1",
                "preset_id": "test",
                "requested_variant_count": 1,
            },
            "outputs": [
                {
                    "output_id": "provider_out",
                    "variant_id": generation_spec["variation_plan"][0]["variant_id"],
                    "image_ref": str(path),
                    "generation_metadata": {"attempt": 1},
                }
            ],
            "warnings": [],
            "errors": [],
        }


class RetryThenPassReviewer:
    def __init__(self):
        self.calls = 0

    def review(self, **kwargs):
        self.calls += 1
        decision = "RETRY" if self.calls == 1 else "PASS"
        return {
            "schema_version": "result_review.v1",
            "review_status": "complete",
            "intensity": "bold",
            "decision": decision,
            "overall_score": 0.95 if decision == "PASS" else 0.60,
            "checks": {},
            "violations": [],
            "retry_recommendation": (
                {"strategy": "restore_requested_intensity_mode"}
                if decision == "RETRY"
                else None
            ),
            "fallback_recommendation": None,
        }


def _planned():
    return {
        "analysis": {"schema_version": "pose_analysis.v1"},
        "plan": {"schema_version": "pose_plan.v1"},
        "target": {
            "schema_version": "pose_target.v1",
            "selected_preset": {"intensity": "bold"},
        },
        "generation_spec": {
            "schema_version": "generation_spec.v1",
            "task": {"output_count": 1},
            "selected_preset": {"preset_id": "test", "intensity": "bold"},
            "variation_plan": [
                {
                    "variant_id": "option_a",
                    "required_intensity": "bold",
                    "mode_consistency_required": True,
                }
            ],
            "retry_policy": {
                "max_attempts_per_slot": 2,
                "targeted_retries_per_failed_slot": 1,
                "request_budget_policy": "initial_batch_plus_one_targeted_retry_per_failed_slot",
            },
            "transform": {"summary": "Apply Bold.", "mechanics": []},
        },
    }


def test_failed_candidate_is_replaced_before_surface(tmp_path):
    image = FakeImageAdapter()
    reviewer = RetryThenPassReviewer()

    result = generate_and_review(
        source_image_path=str(tmp_path / "source.jpg"),
        planned=_planned(),
        image_adapter=image,
        review_adapter=reviewer,
        output_dir=str(tmp_path / "outputs"),
    )

    assert image.calls == 2
    assert reviewer.calls == 2
    assert result["generation"]["generation_status"] == "success"
    assert len(result["generation"]["outputs"]) == 1
    assert result["generation"]["outputs"][0]["generation_metadata"]["attempt"] == 2
    assert result["reviews"][0]["decision"] == "PASS"
    assert result["attempt_log"][0]["decision"] == "RETRY"
    assert result["attempt_log"][1]["decision"] == "PASS"


class DuplicateThenDistinctReviewer:
    def __init__(self):
        self.review_calls = 0
        self.compare_calls = 0

    def review(self, **kwargs):
        self.review_calls += 1
        return {
            "schema_version": "result_review.v1",
            "review_status": "complete",
            "intensity": "bold",
            "decision": "PASS",
            "overall_score": 0.96,
            "checks": {},
            "violations": [],
            "retry_recommendation": None,
            "fallback_recommendation": None,
        }

    def compare_variants(self, **kwargs):
        self.compare_calls += 1
        if self.compare_calls == 1:
            return {"distinctness_score": 0.30, "materially_distinct": False}
        return {"distinctness_score": 0.92, "materially_distinct": True}


def test_duplicate_variant_is_retried_until_distinct(tmp_path):
    planned = _planned()
    planned["generation_spec"]["task"]["output_count"] = 2
    planned["generation_spec"]["variation_plan"] = [
        {
            "variant_id": "option_a",
            "required_intensity": "bold",
            "mode_consistency_required": True,
        },
        {
            "variant_id": "option_b",
            "required_intensity": "bold",
            "mode_consistency_required": True,
        },
    ]

    image = FakeImageAdapter()
    reviewer = DuplicateThenDistinctReviewer()
    result = generate_and_review(
        source_image_path=str(tmp_path / "source.jpg"),
        planned=planned,
        image_adapter=image,
        review_adapter=reviewer,
        output_dir=str(tmp_path / "outputs"),
    )

    assert result["generation"]["generation_status"] == "success"
    assert len(result["generation"]["outputs"]) == 2
    assert any(
        item.get("reason") == "insufficient_variant_distinctness"
        for item in result["attempt_log"]
    )


def test_retry_policy_is_cost_bounded_to_one_targeted_retry():
    planned = _planned()
    policy = planned["generation_spec"]["retry_policy"]

    assert policy["max_attempts_per_slot"] == 2
    assert policy["targeted_retries_per_failed_slot"] == 1
    assert policy["request_budget_policy"] == (
        "initial_batch_plus_one_targeted_retry_per_failed_slot"
    )
