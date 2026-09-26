from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from .openai_structured import POSE_ANALYSIS_FORMAT
from .vision_base import VisionAnalysisAdapter


class OpenAIVisionAdapter(VisionAnalysisAdapter):
    name = "openai"

    def __init__(self, model: str = "gpt-5.6-sol") -> None:
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
            "Analyze exactly one primary human subject for PoseFix. "
            "Describe only visible pose mechanics. Preserve working elements. "
            "Use calibrated severity and confidence. Do not evaluate attractiveness, "
            "body size, or style quality. If the image is unsuitable, use an "
            "unsupported or failed analysis status rather than inventing anatomy."
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
            text={"format": POSE_ANALYSIS_FORMAT},
        )
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise RuntimeError(
                "OpenAI vision response did not contain structured output_text"
            )

        try:
            return json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "OpenAI vision structured output was not valid JSON"
            ) from exc
