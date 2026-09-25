from pathlib import Path
from posefix.adapters.mock_vision import MockVisionAdapter
from posefix.pipeline import analyze_and_plan

def test_fixture_backed_analysis_pipeline():
    root=Path(__file__).parents[1]; fixture=root/"examples"/"test-portrait"/"pose_analysis.json"; image=root/"examples"/"test-portrait"/"placeholder.jpg"
    result=analyze_and_plan(source_image_path=str(image),vision_adapter=MockVisionAdapter(str(fixture)))
    assert result["analysis"]["schema_version"]=="pose_analysis.v1"
    assert result["plan"]["selection_status"]=="selected"
    assert result["target"]["schema_version"]=="pose_target.v1"
    assert result["generation_spec"]["schema_version"]=="generation_spec.v1"
