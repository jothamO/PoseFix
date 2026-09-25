from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PRESET_DIR = ROOT / "presets"


def load_presets() -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text())
        for path in sorted(PRESET_DIR.glob("*.json"))
    ]


def preset_map() -> dict[str, dict[str, Any]]:
    return {preset["preset_id"]: preset for preset in load_presets()}
