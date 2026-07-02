from __future__ import annotations

import json
from pathlib import Path

from reports.generator import render_markdown_report
from reports.models import SecurityReport


def save_report_json(report: SecurityReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output_path


def save_report_markdown(report: SecurityReport, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(report), encoding="utf-8")
    return output_path
