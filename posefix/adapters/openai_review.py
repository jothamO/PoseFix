from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from ..engine.review import decide_review
from .openai_structured import REVIEW_SCORES_FORMAT
from .review_base import ResultReviewAdapter


class OpenAIReviewAdapter(ResultReviewAdapter):
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
    def _prompt(
        pose_target: dict[str, Any],
        generation_spec: dict[str, Any],
    ) -> str:
        return (
            "Compare IMAGE 1 (authoritative source) with IMAGE 2 (generated edit). "
            "Judge execution against the requested PoseFix target, not beauty. "
            "Return normalized scores from 0 to 1 for every required review check "
            "and list only concrete hard violations that are visibly present. "
            "Do not decide PASS/RETRY/FALLBACK/REJECT; deterministic PoseFix engine "
            "code will make that decision. "
            f"POSE TARGET: {json.dumps(pose_target, separators=(',', ':'))} "
            f"GENERATION SPEC: {json.dumps(generation_spec, separators=(',', ':'))}"
        )

    def review(
        self,
        *,
        source_image_path: str,
        generated_image_path: str,
        pose_target: dict[str, Any],
        generation_spec: dict[str, Any],
    ) -> dict[str, Any]:
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
                        {
                            "type": "input_text",
                            "text": self._prompt(pose_target, generation_spec),
                        },
                        {
                            "type": "input_image",
                            "image_url": self._data_url(source_image_path),
                            "detail": "high",
                        },
                        {
                            "type": "input_image",
                            "image_url": self._data_url(generated_image_path),
                            "detail": "high",
                        },
                    ],
                }
            ],
            text={"format": REVIEW_SCORES_FORMAT},
        )
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise RuntimeError(
                "OpenAI review response did not contain structured output_text"
            )

        try:
            structured = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "OpenAI review structured output was not valid JSON"
            ) from exc

        return decide_review(
            structured["scores"],
            structured["violations"],
        )
