from __future__ import annotations

POSE_ANALYSIS_FORMAT = {
    "type": "json_schema",
    "name": "pose_analysis_v1",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "analysis_status",
            "image",
            "subject",
            "diagnosis",
            "edit_plan",
            "feasibility",
        ],
        "properties": {
            "schema_version": {"type": "string", "enum": ["pose_analysis.v1"]},
            "analysis_status": {
                "type": "string",
                "enum": ["success", "unsupported", "failed"],
            },
            "image": {
                "type": "object",
                "additionalProperties": False,
                "required": ["subject_count", "crop"],
                "properties": {
                    "subject_count": {"type": "integer", "minimum": 0},
                    "crop": {
                        "type": "string",
                        "enum": [
                            "close_up",
                            "head_shoulders",
                            "half_body",
                            "three_quarter",
                            "full_body",
                            "unknown",
                        ],
                    },
                },
            },
            "subject": {
                "type": "object",
                "additionalProperties": False,
                "required": ["pose_type", "support_context", "visibility"],
                "properties": {
                    "pose_type": {
                        "type": "string",
                        "enum": [
                            "standing",
                            "seated",
                            "leaning",
                            "walking",
                            "crouching",
                            "lying",
                            "transitional",
                            "unknown",
                        ],
                    },
                    "support_context": {"type": "string"},
                    "visibility": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "face",
                            "neck",
                            "shoulders",
                            "torso",
                            "elbows",
                            "hands",
                            "hips",
                            "knees",
                            "feet",
                        ],
                        "properties": {
                            region: {
                                "type": "string",
                                "enum": [
                                    "fully_visible",
                                    "partially_visible",
                                    "occluded",
                                    "outside_frame",
                                    "uncertain",
                                ],
                            }
                            for region in [
                                "face",
                                "neck",
                                "shoulders",
                                "torso",
                                "elbows",
                                "hands",
                                "hips",
                                "knees",
                                "feet",
                            ]
                        },
                    },
                },
            },
            "diagnosis": {
                "type": "object",
                "additionalProperties": False,
                "required": ["working_elements", "issues"],
                "properties": {
                    "working_elements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["mechanic", "reason", "confidence"],
                            "properties": {
                                "mechanic": {"type": "string"},
                                "reason": {"type": "string"},
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                        },
                    },
                    "issues": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "id",
                                "mechanic",
                                "severity",
                                "confidence",
                            ],
                            "properties": {
                                "id": {"type": "string"},
                                "mechanic": {"type": "string"},
                                "severity": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "confidence": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                            },
                        },
                    },
                },
            },
            "edit_plan": {
                "type": "object",
                "additionalProperties": False,
                "required": ["preserve", "adjust", "avoid"],
                "properties": {
                    "preserve": {"type": "array", "items": {"type": "string"}},
                    "adjust": {"type": "array", "items": {"type": "string"}},
                    "avoid": {"type": "array", "items": {"type": "string"}},
                },
            },
            "feasibility": {
                "type": "object",
                "additionalProperties": False,
                "required": ["overall"],
                "properties": {
                    "overall": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    }
                },
            },
        },
    },
}

REVIEW_SCORES_FORMAT = {
    "type": "json_schema",
    "name": "posefix_review_scores",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["scores", "violations"],
        "properties": {
            "scores": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "identity_retention",
                    "pose_target_adherence",
                    "anatomical_plausibility",
                    "hand_quality",
                    "clothing_retention",
                    "accessory_retention",
                    "background_retention",
                    "lighting_consistency",
                    "ground_contact",
                    "body_shape_preservation",
                    "expression_preservation",
                ],
                "properties": {
                    name: {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                    }
                    for name in [
                        "identity_retention",
                        "pose_target_adherence",
                        "anatomical_plausibility",
                        "hand_quality",
                        "clothing_retention",
                        "background_retention",
                        "lighting_consistency",
                        "ground_contact",
                        "body_shape_preservation",
                        "expression_preservation",
                    ]
                },
            },
            "violations": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    },
}
