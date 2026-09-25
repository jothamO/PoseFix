from pathlib import Path
from posefix.adapters import MockImageAdapter, MockReviewAdapter, MockVisionAdapter
from posefix.pipeline import analyze_and_plan, generate_and_review

def test_full_mock_pipeline(tmp_path):
    root=Path(__file__).parents[1]; fixture=root/"examples"/"test-portrait"/"pose_analysis.json"; image=root/"examples"/"test-portrait"/"placeholder.jpg"
    planned=analyze_and_plan(source_image_path=str(image),vision_adapter=MockVisionAdapter(str(fixture)))
    result=generate_and_review(source_image_path=str(image),planned=planned,image_adapter=MockImageAdapter(),review_adapter=MockReviewAdapter(),output_dir=str(tmp_path))
    assert result["generation"]["generation_status"]=="success"
    assert result["reviews"][0]["decision"]=="PASS"
