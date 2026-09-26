from __future__ import annotations

from typing import Any

from .review_base import ResultReviewAdapter


class MockReviewAdapter(ResultReviewAdapter):
    """Deterministic PASS reviewer for orchestration tests only."""

    name = "mock"

    def review(self, *, source_image_path: str, generated_image_path: str, pose_target: dict[str, Any], generation_spec: dict[str, Any]) -> dict[str, Any]:
        _ = (source_image_path, generated_image_path, pose_target, generation_spec)
        checks = {key: {"score": 1.0, "status": "pass", "confidence": 1.0} for key in ["identity_retention","pose_target_adherence","anatomical_plausibility","hand_quality","clothing_retention","accessory_retention","background_retention","lighting_consistency","ground_contact","body_shape_preservation","expression_preservation"]}
        return {"schema_version":"result_review.v1","review_status":"complete","output_id":"out_001","decision":"PASS","overall_score":1.0,"checks":checks,"violations":[],"retry_recommendation":None,"fallback_recommendation":None}
