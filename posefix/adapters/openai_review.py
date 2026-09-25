from __future__ import annotations

import base64, json, mimetypes, os
from pathlib import Path
from typing import Any
from .review_base import ResultReviewAdapter

class OpenAIReviewAdapter(ResultReviewAdapter):
    name = "openai"
    def __init__(self, model: str = "gpt-5.6-luna") -> None: self.model = model
    @staticmethod
    def _data_url(path: str) -> str:
        p=Path(path); mime=mimetypes.guess_type(p.name)[0] or "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('ascii')}"
    @staticmethod
    def _prompt(pose_target: dict[str, Any], generation_spec: dict[str, Any]) -> str:
        return ("You are the PoseFix result-review skill. Compare IMAGE 1 (authoritative source) with IMAGE 2 (generated edit). Judge execution, not beauty. Return ONLY valid JSON matching result_review.v1. Decision must be PASS, RETRY, FALLBACK, or REJECT. Check identity retention, pose target adherence, anatomical plausibility, hand quality, clothing retention, background retention, lighting consistency, ground contact, body shape preservation, and expression preservation. " + f"POSE TARGET: {json.dumps(pose_target,separators=(',',':'))} GENERATION SPEC: {json.dumps(generation_spec,separators=(',',':'))}")
    def review(self, *, source_image_path: str, generated_image_path: str, pose_target: dict[str, Any], generation_spec: dict[str, Any]) -> dict[str, Any]:
        if not os.getenv("OPENAI_API_KEY"): raise RuntimeError("OPENAI_API_KEY is not set")
        try: from openai import OpenAI
        except ImportError as exc: raise RuntimeError("Install PoseFix with `pip install -e .[openai]`") from exc
        response=OpenAI().responses.create(model=self.model,input=[{"role":"user","content":[{"type":"input_text","text":self._prompt(pose_target,generation_spec)},{"type":"input_image","image_url":self._data_url(source_image_path),"detail":"high"},{"type":"input_image","image_url":self._data_url(generated_image_path),"detail":"high"}]}])
        text=getattr(response,"output_text",None)
        if not text: raise RuntimeError("OpenAI review response did not contain output_text")
        try: return json.loads(text)
        except json.JSONDecodeError as exc: raise RuntimeError("OpenAI review response was not valid JSON") from exc
