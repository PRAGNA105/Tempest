from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scanners import URLScanner, save_findings_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repository for URLs.")
    parser.add_argument("repository", type=Path, help="Repository path to scan.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("state") / "url_findings.json",
        help="Path to write URL findings JSON.",
    )
    args = parser.parse_args()

    findings = URLScanner().scan(args.repository)
    output = save_findings_json(findings, args.output)
    print(f"Wrote {len(findings)} URL findings to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
