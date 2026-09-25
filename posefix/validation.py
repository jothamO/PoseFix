from __future__ import annotations
import json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parent.parent
SCHEMAS=ROOT/"schemas"
def validate_contract(payload:dict[str,Any])->None:
    try: import jsonschema
    except ImportError as exc: raise RuntimeError("jsonschema is required to validate PoseFix contracts") from exc
    version=payload.get("schema_version")
    if not version: raise ValueError("Missing schema_version")
    path=SCHEMAS/f"{version}.json"
    if not path.exists(): raise ValueError(f"Unknown PoseFix contract: {version}")
    jsonschema.validate(payload,json.loads(path.read_text()))
