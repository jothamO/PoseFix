"""Experimental multi-person representation and planning for PoseFix."""

from .experiments import (
    build_group_generation_spec,
    build_progressive_steps,
    choose_generation_strategy,
    summarize_experiment_result,
)
from .planner import (
    adapt_template,
    build_group_target,
    classify_compatibility,
    estimate_reconstruction_debt,
    map_reference_roles,
    recommend_templates,
)
from .templates import GROUP_TEMPLATES

__all__ = [
    "GROUP_TEMPLATES",
    "build_group_generation_spec",
    "build_progressive_steps",
    "choose_generation_strategy",
    "adapt_template",
    "build_group_target",
    "classify_compatibility",
    "estimate_reconstruction_debt",
    "map_reference_roles",
    "recommend_templates",
    "summarize_experiment_result",
]
