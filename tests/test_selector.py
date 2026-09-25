import copy
import json
from pathlib import Path

from posefix.engine import build_generation_spec, build_pose_target, choose_plan
from posefix.registry import load_presets, preset_map


def fixture():
    path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "test-portrait"
        / "pose_analysis.json"
    )
    return json.loads(path.read_text())


def test_reference_portrait_selects_locked_composite():
    plan = choose_plan(fixture(), load_presets())

    assert plan["selection_status"] == "selected"
    assert plan["label"] == "Natural Upgrade"
    assert plan["components"] == [
        {
            "preset_id": "soft_weight_shift",
            "role": "primary",
            "weight": 1.0,
        },
        {
            "preset_id": "turned_slightly",
            "role": "secondary",
            "weight": 0.35,
        },
    ]


def test_preserves_original_when_no_correction_is_supported():
    analysis = copy.deepcopy(fixture())
    analysis["diagnosis"]["issues"] = []

    plan = choose_plan(analysis, load_presets())

    assert plan["selection_status"] == "no_strong_correction"
    assert plan["recommendation"] == "preserve_original"
    assert plan["components"] == []


def test_builds_target_and_generation_spec():
    analysis = fixture()
    plan = choose_plan(analysis, load_presets())
    target = build_pose_target(analysis, plan, preset_map())
    spec = build_generation_spec(target)
    assert spec["schema_version"] == "generation_spec.v1"


def test_analysis_contract_validates():
    from posefix.validation import validate_contract

    validate_contract(fixture())


def test_already_good_pose_returns_preserve_original():
    analysis = copy.deepcopy(fixture())
    analysis["diagnosis"]["issues"] = [
        {
            "id": "centered_weight",
            "mechanic": "weight_distribution",
            "severity": 0.30,
            "confidence": 0.90,
        }
    ]

    plan = choose_plan(analysis, load_presets())

    assert plan["selection_status"] == "no_strong_correction"
    assert plan["recommendation"] == "preserve_original"
    assert plan["reason"] == "already_good_pose"
    assert plan["components"] == []


def test_meaningful_issue_still_selects_correction():
    analysis = copy.deepcopy(fixture())
    analysis["diagnosis"]["issues"] = [
        {
            "id": "centered_weight",
            "mechanic": "weight_distribution",
            "severity": 0.60,
            "confidence": 0.90,
        }
    ]

    plan = choose_plan(analysis, load_presets())

    assert plan["selection_status"] == "selected"
