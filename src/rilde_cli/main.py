from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rilde_cli.pipeline import run_deterministic_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run(args)

    parser.print_help()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rilde",
        description="Repository Intelligence and Leak Detection Engine.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Run the deterministic repository intelligence pipeline.",
    )
    run_parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository path to scan.",
    )
    run_parser.add_argument(
        "--graph-json",
        type=Path,
        default=None,
        help="Graphify NetworkX node-link graph JSON path.",
    )
    run_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("state"),
        help="Directory for deterministic pipeline artifacts.",
    )

    return parser


def _run(args: argparse.Namespace) -> int:
    try:
        result = run_deterministic_pipeline(
            args.repository,
            graph_json=args.graph_json,
            output_dir=args.output_dir,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"rilde: {exc}", file=sys.stderr)
        return 1

    print("RILDE deterministic pipeline complete.")
    print(f"Graph nodes: {result.counts['graph_nodes']}")
    print(f"Scanner findings: {result.counts['scanner_findings']}")
    print(f"Environment candidates: {result.counts['environment_candidates']}")
    print(f"Boundary candidates: {result.counts['boundary_candidates']}")
    print(f"Leak findings: {result.counts['leak_findings']}")
    print(f"Report JSON: {result.paths['report_json']}")
    print(f"Report Markdown: {result.paths['report_markdown']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
