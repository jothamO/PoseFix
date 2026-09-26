from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from .base import AdapterCapabilities


class OpenAIImageAdapter:
    """Thin OpenAI image-edit adapter; provider details stay inside this adapter."""

    name = "openai"

    def __init__(self, model: str = "gpt-image-2.5-sunburst") -> None:
        self.model = model

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            image_edit=True,
            masking=True,
            identity_reference=True,
        )

    def validate(self, generation_spec: dict[str, Any]) -> list[str]:
        _ = generation_spec
        return [] if os.getenv("OPENAI_API_KEY") else ["OPENAI_API_KEY is not set"]

    @staticmethod
    def _prompt(spec: dict[str, Any]) -> str:
        preserve = ", ".join(spec.get("preservation_hierarchy", []))
        mechanics = "; ".join(
            f"{item['mechanic']}: {item['action']} "
            f"(strength {item.get('strength', 'n/a')})"
            for item in spec.get("transform", {}).get("mechanics", [])
        )
        negatives = ", ".join(spec.get("negative_constraints", []))
        summary = spec.get("transform", {}).get(
            "summary",
            "Apply the requested pose correction.",
        )
        return (
            "Use the supplied photograph as the authoritative source. "
            f"{summary} Preserve strictly: {preserve}. "
            f"Requested pose mechanics: {mechanics}. "
            f"Do not: {negatives}. "
            "Keep the same person, clothing, background, lighting, camera perspective, "
            "and photographic moment except for the minimum necessary pose correction."
        )

    def generate(
        self,
        *,
        source_image_path: str,
        generation_spec: dict[str, Any],
        output_dir: str,
    ) -> dict[str, Any]:
        problems = self.validate(generation_spec)
        if problems:
            return {
                "schema_version": "generation_result.v1",
                "generation_status": "provider_error",
                "provider": {
                    "name": self.name,
                    "adapter_version": "0.1.0",
                    "model": self.model,
                },
                "request": {
                    "generation_spec_version": generation_spec["schema_version"],
                    "preset_id": generation_spec["selected_preset"]["preset_id"],
                    "requested_variant_count": 1,
                },
                "outputs": [],
                "warnings": [],
                "errors": problems,
            }

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Install PoseFix with `pip install -e .[openai]`"
            ) from exc

        client = OpenAI()
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        with open(source_image_path, "rb") as image_file:
            result = client.images.edit(
                model=self.model,
                image=image_file,
                prompt=self._prompt(generation_spec),
                quality="high",
            )

        item = result.data[0]
        encoded = getattr(item, "b64_json", None)
        if not encoded:
            raise RuntimeError("OpenAI image edit did not return b64_json")

        target = out_dir / "openai_out_001.png"
        target.write_bytes(base64.b64decode(encoded))

        return {
            "schema_version": "generation_result.v1",
            "generation_status": "success",
            "provider": {
                "name": self.name,
                "adapter_version": "0.1.0",
                "model": self.model,
            },
            "request": {
                "generation_spec_version": generation_spec["schema_version"],
                "preset_id": generation_spec["selected_preset"]["preset_id"],
                "requested_variant_count": 1,
            },
            "outputs": [
                {
                    "output_id": "out_001",
                    "variant_id": "natural",
                    "image_ref": str(target),
                    "generation_metadata": {
                        "attempt": 1,
                        "provider_request_id": getattr(result, "id", None),
                        "seed": None,
                    },
                }
            ],
            "warnings": [],
            "errors": [],
        }
