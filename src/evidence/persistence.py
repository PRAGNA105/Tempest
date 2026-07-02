from __future__ import annotations

import json
from pathlib import Path

from evidence.models import EvidenceRecord


def save_evidence_json(records: list[EvidenceRecord], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [record.model_dump(mode="json") for record in records]
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
