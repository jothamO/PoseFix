"""Experimental multi-person representation and planning for PoseFix."""

from .planner import (
    classify_compatibility,
    map_reference_roles,
    recommend_templates,
)
from .templates import GROUP_TEMPLATES

__all__ = [
    "GROUP_TEMPLATES",
    "classify_compatibility",
    "map_reference_roles",
    "recommend_templates",
]
