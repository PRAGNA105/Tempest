from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scanners import CloudResourceScanner, save_findings_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a repository for cloud resource references.")
    parser.add_argument("repository", type=Path, help="Repository path to scan.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("state") / "cloud_findings.json",
        help="Path to write cloud resource findings JSON.",
    )
    args = parser.parse_args()

    findings = CloudResourceScanner().scan(args.repository)
    output = save_findings_json(findings, args.output)
    print(f"Wrote {len(findings)} cloud resource findings to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
