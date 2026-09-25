from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResultReviewAdapter(ABC):
    name: str

    @abstractmethod
    def review(self, *, source_image_path: str, generated_image_path: str, pose_target: dict[str, Any], generation_spec: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
