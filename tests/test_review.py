from posefix.engine.review import decide_review

def test_pass_review():
    checks={"identity_retention":0.97,"pose_target_adherence":0.91,"anatomical_plausibility":0.96,"hand_quality":0.94,"clothing_retention":0.95,"background_retention":0.98,"lighting_consistency":0.96,"ground_contact":0.95,"body_shape_preservation":0.98,"expression_preservation":0.97}
    assert decide_review(checks,[])["decision"]=="PASS"

def test_hard_violation_rejects():
    assert decide_review({"identity_retention":0.99},["extra_limb"])["decision"]=="REJECT"
