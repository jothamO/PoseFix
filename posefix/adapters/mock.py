from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import AdapterCapabilities


class MockAdapter:
    """Deterministic adapter used for engine tests.

    It does not modify pixels. It returns the source image as a synthetic
    generation result so orchestration can be tested without inference cost.
    """

    name = "mock"

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(local_execution=True)

    def validate(self, generation_spec: dict[str, Any]) -> list[str]:
        return []

    def generate(self, *, source_image_path: str, generation_spec: dict[str, Any], output_dir: str) -> dict[str, Any]:
        src = Path(source_image_path)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        target = out / f"mock_{src.name}"
        target.write_bytes(src.read_bytes())
        return {
            "schema_version": "generation_result.v1",
            "generation_status": "success",
            "provider": {"name": self.name, "adapter_version": "0.1.0", "model": "none"},
            "request": {
                "generation_spec_version": generation_spec["schema_version"],
                "preset_id": generation_spec["selected_preset"]["preset_id"],
                "requested_variant_count": 1,
            },
            "outputs": [{"output_id":"out_001","variant_id":"natural","image_ref":str(target),"generation_metadata":{"attempt":1,"provider_request_id":None,"seed":None}}],
            "warnings": ["Mock adapter returns the original image unchanged."],
            "errors": [],
        }
