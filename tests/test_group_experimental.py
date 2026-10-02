from posefix.experimental.group import (
    classify_compatibility,
    map_reference_roles,
    recommend_templates,
)


def test_recommends_templates_without_spending_on_generation():
    analysis = {
        "people_count": 4,
        "body_visibility": "full_body",
        "horizontal_space": "high",
        "occlusion_complexity": "low",
        "depth_cues": "moderate",
    }

    results = recommend_templates(analysis, limit=3)

    assert len(results) == 3
    assert all(item["compatibility_score"] > 0 for item in results)
    assert all("template_id" in item for item in results)


def test_layered_editorial_is_penalized_when_depth_cues_are_low():
    analysis = {
        "people_count": 4,
        "body_visibility": "upper_body",
        "horizontal_space": "medium",
        "occlusion_complexity": "medium",
        "depth_cues": "low",
    }

    results = recommend_templates(analysis, limit=6)
    editorial = next(
        item for item in results if item["template_id"] == "layered_editorial"
    )

    assert editorial["compatibility_score"] < 0.8
    assert "insufficient_depth_cues" in editorial["reasons"]


def test_reference_mapping_is_geometry_only():
    people = [
        {"person_id": "p1", "x": 0.2, "body_visibility": "full_body"},
        {"person_id": "p2", "x": 0.8, "body_visibility": "full_body"},
    ]
    slots = [
        {"slot_id": "left", "x": 0.15, "required_visibility": "full_body"},
        {"slot_id": "right", "x": 0.85, "required_visibility": "full_body"},
    ]

    mapped = map_reference_roles(people, slots)

    assert mapped[0]["person_id"] == "p1"
    assert mapped[0]["slot_id"] == "left"
    assert mapped[0]["mapping_basis"] == "geometry_only"
    assert mapped[1]["person_id"] == "p2"
    assert mapped[1]["slot_id"] == "right"


def test_compatibility_bands():
    assert classify_compatibility(0.9) == "compatible"
    assert classify_compatibility(0.7) == "adaptable"
    assert classify_compatibility(0.3) == "high_risk"
    assert classify_compatibility(0.0) == "unsupported"
