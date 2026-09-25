from __future__ import annotations
from typing import Any
HARD_VIOLATIONS={"identity_drift","extra_limb","missing_limb","severe_hand_failure","body_reshape_detected","major_clothing_redesign","background_replacement","floating_subject","broken_ground_contact","age_change","skin_tone_change"}
THRESHOLDS={"identity_retention":0.90,"pose_target_adherence":0.80,"anatomical_plausibility":0.90,"hand_quality":0.85,"clothing_retention":0.90,"background_retention":0.90,"lighting_consistency":0.88,"ground_contact":0.90,"body_shape_preservation":0.95,"expression_preservation":0.90}
def decide_review(checks:dict[str,float],violations:list[str])->dict[str,Any]:
    hard=sorted(HARD_VIOLATIONS.intersection(violations)); normalized={k:{"score":float(v),"status":"pass" if float(v)>=THRESHOLDS.get(k,0.0) else "fail","confidence":1.0} for k,v in checks.items()}
    if hard: decision="REJECT"
    else:
        failed=[k for k,v in normalized.items() if v["status"]=="fail"]
        decision="PASS" if not failed else ("RETRY" if any(k in failed for k in {"identity_retention","anatomical_plausibility","hand_quality"}) else "FALLBACK")
    overall=sum(v["score"] for v in normalized.values())/max(len(normalized),1)
    return {"schema_version":"result_review.v1","review_status":"complete","decision":decision,"overall_score":round(overall,4),"checks":normalized,"violations":violations,"retry_recommendation":{"strategy":"reduce_pose_strength"} if decision=="RETRY" else None,"fallback_recommendation":{"target":"lower_intensity","intensity":"subtle"} if decision=="FALLBACK" else None}
