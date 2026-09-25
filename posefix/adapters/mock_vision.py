from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .vision_base import VisionAnalysisAdapter


class MockVisionAdapter(VisionAnalysisAdapter):
    """Deterministic fixture-backed vision adapter for tests and demos."""

    name = "mock"

    def __init__(self, fixture_path: str) -> None:
        self.fixture_path = Path(fixture_path)

    def analyze(self, *, source_image_path: str) -> dict[str, Any]:
        _ = source_image_path
        return json.loads(self.fixture_path.read_text())
