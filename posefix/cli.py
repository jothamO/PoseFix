from __future__ import annotations
import argparse, json
from pathlib import Path
from .adapters import MockVisionAdapter, OpenAIImageAdapter, OpenAIReviewAdapter, OpenAIVisionAdapter
from .engine import build_generation_spec, build_pose_target, choose_plan
from .pipeline import analyze_and_plan, generate_and_review
from .registry import load_presets, preset_map

def _load(path:str)->dict: return json.loads(Path(path).read_text())
def _dump(payload:dict,path:str|None)->None:
    text=json.dumps(payload,indent=2)
    if path: Path(path).write_text(text+"\n")
    else: print(text)

def cmd_plan(args):
    analysis=_load(args.analysis); plan=choose_plan(analysis,load_presets()); target=build_pose_target(analysis,plan,preset_map()) if plan.get("selection_status")=="selected" else None; _dump({"plan":plan,"target":target},args.output); return 0

def cmd_spec(args):
    analysis=_load(args.analysis); plan=choose_plan(analysis,load_presets())
    if plan.get("selection_status")!="selected": _dump({"plan":plan,"generation_spec":None},args.output); return 0
    _dump(build_generation_spec(build_pose_target(analysis,plan,preset_map())),args.output); return 0

def _vision_adapter(args):
    if args.vision_provider=="mock":
        if not args.fixture: raise SystemExit("--fixture is required for --vision-provider mock")
        return MockVisionAdapter(args.fixture)
    if args.vision_provider=="openai": return OpenAIVisionAdapter(model=args.vision_model)
    raise SystemExit(f"Unsupported vision provider: {args.vision_provider}")

def cmd_analyze(args): _dump(analyze_and_plan(source_image_path=args.image,vision_adapter=_vision_adapter(args)),args.output); return 0

def cmd_run(args):
    planned=analyze_and_plan(source_image_path=args.image,vision_adapter=_vision_adapter(args))
    if args.image_provider=="none": _dump(planned,args.output); return 0
    image_adapter=OpenAIImageAdapter(model=args.image_model); reviewer=OpenAIReviewAdapter(model=args.review_model) if args.review_provider=="openai" else None
    _dump(generate_and_review(source_image_path=args.image,planned=planned,image_adapter=image_adapter,review_adapter=reviewer,output_dir=args.output_dir),args.output); return 0

def _add_vision_args(p): p.add_argument("--vision-provider",choices=["mock","openai"],default="mock"); p.add_argument("--vision-model",default="gpt-5.6-luna"); p.add_argument("--fixture")
def main()->int:
    parser=argparse.ArgumentParser(prog="posefix"); sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("plan"); p.add_argument("analysis"); p.add_argument("-o","--output"); p.set_defaults(func=cmd_plan)
    p=sub.add_parser("spec"); p.add_argument("analysis"); p.add_argument("-o","--output"); p.set_defaults(func=cmd_spec)
    p=sub.add_parser("analyze"); p.add_argument("image"); _add_vision_args(p); p.add_argument("-o","--output"); p.set_defaults(func=cmd_analyze)
    p=sub.add_parser("run"); p.add_argument("image"); _add_vision_args(p); p.add_argument("--image-provider",choices=["none","openai"],default="none"); p.add_argument("--image-model",default="gpt-image-2"); p.add_argument("--review-provider",choices=["none","openai"],default="none"); p.add_argument("--review-model",default="gpt-5.6-luna"); p.add_argument("--output-dir",default="posefix-output"); p.add_argument("-o","--output"); p.set_defaults(func=cmd_run)
    args=parser.parse_args(); return args.func(args)
if __name__=="__main__": raise SystemExit(main())
