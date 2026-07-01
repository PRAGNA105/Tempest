from __future__ import annotations

import json
from pathlib import Path

from scanners.models import Finding


def save_findings_json(findings: list[Finding], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "finding_type": finding.__class__.__name__,
            **finding.model_dump(mode="json"),
        }
        for finding in findings
    ]
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path

