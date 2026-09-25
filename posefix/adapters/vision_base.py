from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VisionAnalysisAdapter(ABC):
    name: str

    @abstractmethod
    def analyze(self, *, source_image_path: str) -> dict[str, Any]:
        raise NotImplementedError
