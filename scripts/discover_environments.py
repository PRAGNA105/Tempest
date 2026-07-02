from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from environment import EnvironmentDiscovery, save_environment_candidates_json
from scanners import CloudResourceFinding, DatabaseFinding, Finding, SecretFinding, URLFinding

FINDING_MODELS = {
    "CloudResourceFinding": CloudResourceFinding,
    "DatabaseFinding": DatabaseFinding,
    "SecretFinding": SecretFinding,
    "URLFinding": URLFinding,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive environment candidates from persisted scanner findings."
    )
    parser.add_argument(
        "--input",
        type=Path,
        action="append",
        dest="inputs",
        default=None,
        help="Scanner findings JSON path. Can be passed multiple times.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("state") / "environment_candidates.json",
        help="Path to write environment candidates JSON.",
    )
    args = parser.parse_args()

    input_paths = args.inputs or [
        Path("state") / "url_findings.json",
        Path("state") / "database_findings.json",
        Path("state") / "cloud_findings.json",
    ]
    findings = _load_findings(input_paths)
    candidates = EnvironmentDiscovery().discover(findings)
    output = save_environment_candidates_json(candidates, args.output)
    print(f"Wrote {len(candidates)} environment candidates to {output}")
    return 0


def _load_findings(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload:
            finding_type = item.pop("finding_type", None)
            model = FINDING_MODELS.get(finding_type)
            if model is None:
                continue
            findings.append(model(**item))
    return findings


if __name__ == "__main__":
    raise SystemExit(main())
