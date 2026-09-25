from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import (
    MockVisionAdapter,
    OpenAIImageAdapter,
    OpenAIReviewAdapter,
    OpenAIVisionAdapter,
)
from .engine import build_generation_spec, build_pose_target, choose_plan
from .pipeline import analyze_and_plan, generate_and_review
from .registry import load_presets, preset_map


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def _dump(payload: dict, path: str | None) -> None:
    text = json.dumps(payload, indent=2)
    if path:
        Path(path).write_text(text + "\n")
    else:
        print(text)


def cmd_plan(args: argparse.Namespace) -> int:
    analysis = _load(args.analysis)
    plan = choose_plan(analysis, load_presets())
    target = None
    if plan.get("selection_status") == "selected":
        target = build_pose_target(analysis, plan, preset_map())
    _dump({"plan": plan, "target": target}, args.output)
    return 0


def cmd_spec(args: argparse.Namespace) -> int:
    analysis = _load(args.analysis)
    plan = choose_plan(analysis, load_presets())
    if plan.get("selection_status") != "selected":
        _dump({"plan": plan, "generation_spec": None}, args.output)
        return 0

    target = build_pose_target(analysis, plan, preset_map())
    _dump(build_generation_spec(target), args.output)
    return 0


def _vision_adapter(args: argparse.Namespace):
    if args.vision_provider == "mock":
        if not args.fixture:
            raise SystemExit("--fixture is required for --vision-provider mock")
        return MockVisionAdapter(args.fixture)

    if args.vision_provider == "openai":
        return OpenAIVisionAdapter(model=args.vision_model)

    raise SystemExit(f"Unsupported vision provider: {args.vision_provider}")


def cmd_analyze(args: argparse.Namespace) -> int:
    _dump(
        analyze_and_plan(
            source_image_path=args.image,
            vision_adapter=_vision_adapter(args),
        ),
        args.output,
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    planned = analyze_and_plan(
        source_image_path=args.image,
        vision_adapter=_vision_adapter(args),
    )
    if args.image_provider == "none":
        _dump(planned, args.output)
        return 0

    image_adapter = OpenAIImageAdapter(model=args.image_model)
    reviewer = None
    if args.review_provider == "openai":
        reviewer = OpenAIReviewAdapter(model=args.review_model)

    _dump(
        generate_and_review(
            source_image_path=args.image,
            planned=planned,
            image_adapter=image_adapter,
            review_adapter=reviewer,
            output_dir=args.output_dir,
        ),
        args.output,
    )
    return 0


def _add_vision_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--vision-provider",
        choices=["mock", "openai"],
        default="mock",
    )
    parser.add_argument("--vision-model", default="gpt-5.6-luna")
    parser.add_argument("--fixture")


def main() -> int:
    parser = argparse.ArgumentParser(prog="posefix")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("analysis")
    plan_parser.add_argument("-o", "--output")
    plan_parser.set_defaults(func=cmd_plan)

    spec_parser = subparsers.add_parser("spec")
    spec_parser.add_argument("analysis")
    spec_parser.add_argument("-o", "--output")
    spec_parser.set_defaults(func=cmd_spec)

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("image")
    _add_vision_args(analyze_parser)
    analyze_parser.add_argument("-o", "--output")
    analyze_parser.set_defaults(func=cmd_analyze)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("image")
    _add_vision_args(run_parser)
    run_parser.add_argument(
        "--image-provider",
        choices=["none", "openai"],
        default="none",
    )
    run_parser.add_argument("--image-model", default="gpt-image-2")
    run_parser.add_argument(
        "--review-provider",
        choices=["none", "openai"],
        default="none",
    )
    run_parser.add_argument("--review-model", default="gpt-5.6-luna")
    run_parser.add_argument("--output-dir", default="posefix-output")
    run_parser.add_argument("-o", "--output")
    run_parser.set_defaults(func=cmd_run)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
