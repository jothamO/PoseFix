from posefix.experimental.group import (
    adapt_template,
    build_group_target,
    classify_compatibility,
    estimate_reconstruction_debt,
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


def test_locked_person_is_preserved_in_target():
    analysis = {
        "people_count": 3,
        "people": [
            {"person_id": "p1", "locked": True},
            {"person_id": "p2", "locked": False},
            {"person_id": "p3", "locked": False},
        ],
        "relationships": [],
        "occlusion_edges": [],
        "horizontal_space": "high",
        "occlusion_complexity": "low",
        "depth_cues": "moderate",
    }

    target = build_group_target(analysis, "triangle")

    assert target["target_status"] == "ready"
    assert target["locked_people"] == ["p1"]
    person = next(
        item
        for item in target["group_pose_graph"]["people"]
        if item["person_id"] == "p1"
    )
    assert person["pose"]["policy"] == "preserve"


def test_reconstruction_debt_forbids_scene_object_invention():
    debt = estimate_reconstruction_debt(
        ["small_spacing_adjustment", "invent_scene_object"]
    )

    assert debt["total"] > 1.0
    assert debt["forbidden_operations"] == ["invent_scene_object"]


def test_forbidden_reconstruction_makes_target_unsupported():
    analysis = {
        "people_count": 3,
        "people": [
            {"person_id": "p1"},
            {"person_id": "p2"},
            {"person_id": "p3"},
        ],
        "relationships": [],
        "occlusion_edges": [],
        "horizontal_space": "high",
        "occlusion_complexity": "low",
        "depth_cues": "moderate",
    }

    target = build_group_target(
        analysis,
        "triangle",
        operations=["invent_scene_object"],
    )

    assert target["target_status"] == "unsupported"
    assert target["compatibility"] == "unsupported"


def test_target_preserves_relationship_and_occlusion_graphs():
    analysis = {
        "people_count": 3,
        "people": [
            {"person_id": "p1"},
            {"person_id": "p2"},
            {"person_id": "p3"},
        ],
        "relationships": [
            {"a": "p1", "b": "p2", "interaction": "proximity"},
        ],
        "occlusion_edges": [
            {"front": "p2", "behind": "p3", "region": "shoulder"},
        ],
        "horizontal_space": "high",
        "occlusion_complexity": "medium",
        "depth_cues": "moderate",
    }

    target = build_group_target(analysis, "triangle")
    graph = target["group_pose_graph"]

    assert graph["relationships"][0]["a"] == "p1"
    assert graph["relationships"][0]["b"] == "p2"
    assert graph["occlusion_edges"][0]["front"] == "p2"
    assert graph["occlusion_edges"][0]["behind"] == "p3"


def test_template_adaptation_marks_extra_slots_optional():
    people = [
        {"person_id": "p1"},
        {"person_id": "p2"},
        {"person_id": "p3"},
        {"person_id": "p4"},
    ]

    adapted = adapt_template("triangle", people)

    assert adapted["status"] == "adapted"
    assert len(adapted["slots"]) == 4
    assert adapted["slots"][0]["requirement"] == "required"
    assert adapted["slots"][3]["requirement"] == "optional"
