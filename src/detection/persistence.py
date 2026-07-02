from __future__ import annotations

import json
from pathlib import Path

from detection.models import LeakFinding


def save_leak_findings_json(findings: list[LeakFinding], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [finding.model_dump(mode="json") for finding in findings]
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
