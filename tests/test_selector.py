import json
from pathlib import Path
from posefix.engine import build_generation_spec, build_pose_target, choose_plan
from posefix.registry import load_presets, preset_map

def fixture(): return json.loads((Path(__file__).resolve().parents[1]/"examples"/"test-portrait"/"pose_analysis.json").read_text())
def test_selects_plan():
    plan=choose_plan(fixture(),load_presets()); assert plan["selection_status"]=="selected"
def test_builds_target_and_generation_spec():
    analysis=fixture(); plan=choose_plan(analysis,load_presets()); target=build_pose_target(analysis,plan,preset_map()); spec=build_generation_spec(target); assert spec["schema_version"]=="generation_spec.v1"
def test_analysis_contract_validates():
    from posefix.validation import validate_contract
    validate_contract(fixture())
