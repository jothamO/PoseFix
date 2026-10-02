"""Experimental multi-person representation and planning for PoseFix."""

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
    "adapt_template",
    "build_group_target",
    "classify_compatibility",
    "estimate_reconstruction_debt",
    "map_reference_roles",
    "recommend_templates",
]
