from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class AdapterCapabilities:
    image_edit: bool = True
    masking: bool = False
    pose_control: bool = False
    identity_reference: bool = False
    seed_control: bool = False
    local_execution: bool = False


class GenerationAdapter(Protocol):
    name: str

    def capabilities(self) -> AdapterCapabilities: ...

    def validate(self, generation_spec: dict[str, Any]) -> list[str]: ...

    def generate(
        self,
        *,
        source_image_path: str,
        generation_spec: dict[str, Any],
        output_dir: str,
    ) -> dict[str, Any]: ...
