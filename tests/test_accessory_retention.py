from posefix.engine.review import decide_review


def test_accessory_loss_retries_instead_of_passing():
    checks = {
        "identity_retention": 0.97,
        "pose_target_adherence": 0.94,
        "anatomical_plausibility": 0.97,
        "hand_quality": 0.96,
        "clothing_retention": 0.98,
        "accessory_retention": 0.40,
        "background_retention": 0.98,
        "lighting_consistency": 0.96,
        "ground_contact": 0.95,
        "body_shape_preservation": 0.98,
        "expression_preservation": 0.97,
    }

    result = decide_review(checks, [], intensity="bold")

    assert result["decision"] == "RETRY"
    assert result["checks"]["accessory_retention"]["status"] == "fail"
