from __future__ import annotations
from dataclasses import dataclass
from typing import Any
RISK_PENALTY={"low":0.0,"medium":0.08,"high":0.18}
@dataclass(frozen=True)
class ScoredPreset: preset_id:str; score:float; reasons:tuple[str,...]
def _issue_contribution(issue,preset): return float(issue.get("severity",0))*float(issue.get("confidence",0)) if issue["id"] in preset.get("issue_matches",[]) else 0.0
def _visibility_score(analysis,preset):
    visibility=analysis["subject"]["visibility"]
    def visible(r):
        if r=="at_least_one_knee": return visibility.get("knees") in {"fully_visible","partially_visible"}
        if r=="at_least_one_hand": return visibility.get("hands") in {"fully_visible","partially_visible"}
        if r in {"at_least_one_elbow","upper_arms"}: return visibility.get("elbows") in {"fully_visible","partially_visible"}
        return visibility.get(r) in {"fully_visible","partially_visible"}
    return 1.0 if all(visible(r) for r in preset.get("required_visible_regions",[])) else 0.0
def score_presets(analysis:dict[str,Any],presets:list[dict[str,Any]])->list[ScoredPreset]:
    issues=analysis["diagnosis"].get("issues",[]); out=[]
    for preset in presets:
        visibility=_visibility_score(analysis,preset); pose=1.0 if analysis["subject"]["pose_type"] in preset.get("supported_pose_types",[]) else 0.0; crop=1.0 if analysis["image"]["crop"] in preset.get("supported_crops",[]) else 0.0
        if 0.0 in {visibility,pose,crop}: continue
        vals=[_issue_contribution(i,preset) for i in issues]; matched=[issues[i]["id"] for i,v in enumerate(vals) if v>0]; issue=max(vals,default=0.0)
        if issue==0: continue
        scene=1.0 if analysis["subject"].get("support_context","none")=="none" else 0.85; feasibility={"high":1.0,"medium":0.7,"low":0.35}.get(analysis.get("feasibility",{}).get("overall","medium"),0.7); preservation=0.0 if preset["preset_id"]=="one_hand_purpose" and any(x.get("mechanic")=="hand_purpose" for x in analysis["diagnosis"].get("working_elements",[])) else 0.9
        score=0.30*issue+0.20*visibility+0.15*pose+0.15*scene+0.10*preservation+0.10*feasibility-RISK_PENALTY.get(preset.get("risk","medium"),0.08); out.append(ScoredPreset(preset["preset_id"],round(max(0,min(score,1)),4),tuple(matched)))
    return sorted(out,key=lambda x:(-x.score,x.preset_id))
COMPATIBLE_SECONDARIES={"straighten_up":{"open_shoulders","chin_gaze_fix"},"relaxed_upright":{"open_shoulders","chin_gaze_fix"},"open_shoulders":{"straighten_up","soft_weight_shift"},"soft_weight_shift":{"turned_slightly","open_shoulders"},"one_hand_purpose":{"relaxed_upright","soft_weight_shift"},"turned_slightly":{"soft_weight_shift","professional_presence"},"casual_confidence":{"chin_gaze_fix"},"professional_presence":{"turned_slightly","chin_gaze_fix"},"editorial_lite":{"chin_gaze_fix"}}
def choose_plan(analysis,presets):
    ranked=score_presets(analysis,presets); strong=[p for p in ranked if p.score>=0.68]
    if not strong: return {"schema_version":"composite_plan.v1","selection_status":"no_strong_correction","recommendation":"preserve_original","components":[],"ranked_candidates":[p.__dict__ for p in ranked]}
    primary=strong[0]; unresolved={i["id"] for i in analysis["diagnosis"].get("issues",[])}-set(primary.reasons); secondary=None
    for c in strong[1:]:
        if c.preset_id in COMPATIBLE_SECONDARIES.get(primary.preset_id,set()) and c.score>=0.70 and unresolved.intersection(c.reasons): secondary=c; break
    components=[{"preset_id":primary.preset_id,"role":"primary","weight":1.0}]; label=next(p["label"] for p in presets if p["preset_id"]==primary.preset_id)
    if secondary: components.append({"preset_id":secondary.preset_id,"role":"secondary","weight":0.35}); label="Natural Upgrade"
    return {"schema_version":"composite_plan.v1","selection_status":"selected","label":label,"components":components,"ranked_candidates":[p.__dict__ for p in ranked],"unresolved_issues":sorted(unresolved)}
