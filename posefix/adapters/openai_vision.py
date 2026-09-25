from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from .vision_base import VisionAnalysisAdapter


class OpenAIVisionAdapter(VisionAnalysisAdapter):
    name = "openai"

    def __init__(self, model: str = "gpt-5.6-luna") -> None:
        self.model = model

    @staticmethod
    def _data_url(path: str) -> str:
        image_path = Path(path)
        mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"

    @staticmethod
    def _prompt() -> str:
        return (
            "You are the PoseFix pose-analysis skill. Analyze exactly one primary "
            "human subject in the supplied photograph. Return ONLY valid JSON for "
            "schema_version pose_analysis.v1. Describe what is visibly present, "
            "identify pose mechanics with calibrated confidence, distinguish working "
            "elements from issues, preserve good mechanics, estimate feasibility "
            "conservatively, and suggest candidate presets without making generation "
            "instructions. If the image cannot be reliably analyzed, return "
            "analysis_status='unsupported' rather than fabricating observations."
        )

    def analyze(self, *, source_image_path: str) -> dict[str, Any]:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Install PoseFix with `pip install -e .[openai]`"
            ) from exc

        response = OpenAI().responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": self._prompt()},
                        {
                            "type": "input_image",
                            "image_url": self._data_url(source_image_path),
                            "detail": "high",
                        },
                    ],
                }
            ],
        )
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise RuntimeError("OpenAI vision response did not contain output_text")

        try:
            return json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("OpenAI vision response was not valid JSON") from exc
