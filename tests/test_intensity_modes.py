import copy
import json
from pathlib import Path

from posefix.engine import build_generation_spec, build_pose_target, choose_plan
from posefix.engine.intensity import get_intensity_policy
from posefix.engine.review import decide_review
from posefix.registry import load_presets, preset_map


def fixture():
    path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "test-portrait"
        / "pose_analysis.json"
    )
    return json.loads(path.read_text())


def test_natural_remains_locked_default():
    plan = choose_plan(fixture(), load_presets())

    assert plan["intensity"] == "natural"
    assert plan["components"][1]["weight"] == 0.35

    target = build_pose_target(fixture(), plan, preset_map())
    assert target["selected_preset"]["intensity"] == "natural"
    assert target["intensity_policy"]["status"] == "locked"
    assert target["intensity_policy"]["pose_adherence_threshold"] == 0.80


def test_enhanced_increases_pose_freedom_without_relaxing_preservation():
    analysis = fixture()
    plan = choose_plan(analysis, load_presets(), intensity="enhanced")
    target = build_pose_target(analysis, plan, preset_map())
    spec = build_generation_spec(target)

    assert plan["intensity"] == "enhanced"
    assert plan["components"][1]["weight"] == 0.50
    assert target["selected_preset"]["intensity"] == "enhanced"
    assert target["intensity_policy"]["mechanic_budget"] == 4
    assert target["intensity_policy"]["pose_adherence_threshold"] == 0.86
    assert target["edit_budget"]["limb_reconstruction_allowance"] == "medium_low"
    assert spec["selected_preset"]["intensity"] == "enhanced"
    assert spec["scene_constraints"]["background"] == "preserve"
    assert spec["protected_regions"][0]["policy"] == "strict_preserve"


def test_enhanced_can_act_on_moderate_signal_natural_preserves():
    analysis = copy.deepcopy(fixture())
    analysis["diagnosis"]["issues"] = [
        {
            "id": "centered_weight",
            "mechanic": "weight_distribution",
            "severity": 0.40,
            "confidence": 0.90,
        }
    ]

    natural = choose_plan(analysis, load_presets(), intensity="natural")
    enhanced = choose_plan(analysis, load_presets(), intensity="enhanced")

    assert natural["recommendation"] == "preserve_original"
    assert enhanced["selection_status"] == "selected"


def test_review_pose_threshold_tracks_intensity():
    checks = {
        "identity_retention": 0.97,
        "pose_target_adherence": 0.84,
        "anatomical_plausibility": 0.97,
        "hand_quality": 0.96,
        "clothing_retention": 0.98,
        "background_retention": 0.98,
        "lighting_consistency": 0.96,
        "ground_contact": 0.95,
        "body_shape_preservation": 0.98,
        "expression_preservation": 0.97,
    }

    assert decide_review(checks, [], intensity="natural")["decision"] == "PASS"
    assert decide_review(checks, [], intensity="enhanced")["decision"] == "RETRY"


def test_bold_is_defined_but_experimental():
    policy = get_intensity_policy("bold")

    assert policy.status == "experimental"
    assert policy.pose_adherence_threshold == 0.90
    assert policy.mechanic_budget == 6
