from posefix.adapters.openai import OpenAIImageAdapter
from posefix.adapters.openai_review import OpenAIReviewAdapter
from posefix.adapters.openai_structured import (
    POSE_ANALYSIS_FORMAT,
    REVIEW_SCORES_FORMAT,
)
from posefix.adapters.openai_vision import OpenAIVisionAdapter


def test_current_openai_defaults():
    assert OpenAIVisionAdapter().model == "gpt-5.6-sol"
    assert OpenAIReviewAdapter().model == "gpt-5.6-sol"
    assert OpenAIImageAdapter().model == "gpt-image-2"


def test_openai_structured_formats_are_strict():
    assert POSE_ANALYSIS_FORMAT["type"] == "json_schema"
    assert POSE_ANALYSIS_FORMAT["strict"] is True
    assert POSE_ANALYSIS_FORMAT["schema"]["additionalProperties"] is False

    assert REVIEW_SCORES_FORMAT["type"] == "json_schema"
    assert REVIEW_SCORES_FORMAT["strict"] is True
    assert REVIEW_SCORES_FORMAT["schema"]["additionalProperties"] is False


def test_review_format_requires_all_engine_checks():
    required = set(
        REVIEW_SCORES_FORMAT["schema"]["properties"]["scores"]["required"]
    )
    assert required == {
        "identity_retention",
        "pose_target_adherence",
        "anatomical_plausibility",
        "hand_quality",
        "clothing_retention",
        "background_retention",
        "lighting_consistency",
        "ground_contact",
        "body_shape_preservation",
        "expression_preservation",
    }
