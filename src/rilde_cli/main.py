from __future__ import annotations

import argparse
import sys
from pathlib import Path

from graphify_adapter import GraphifyCliError
from rilde_cli.pipeline import run_deterministic_pipeline
from rim import validate_rim_json


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run(args)
    if args.command == "validate-rim":
        return _validate_rim(args)

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
    run_parser.add_argument(
        "--graphify-command",
        nargs=argparse.REMAINDER,
        default=None,
        help=(
            "Optional Graphify command to run before the pipeline. Supports "
            "{repository}, {graph_json}, and {graphify_output_dir}; must be last."
        ),
    )

    validate_parser = subparsers.add_parser(
        "validate-rim",
        help="Validate a persisted RIM JSON artifact.",
    )
    validate_parser.add_argument(
        "rim_json",
        nargs="?",
        type=Path,
        default=Path("state") / "rim.json",
        help="RIM JSON path to validate.",
    )

    return parser


def _run(args: argparse.Namespace) -> int:
    try:
        result = run_deterministic_pipeline(
            args.repository,
            graph_json=args.graph_json,
            output_dir=args.output_dir,
            graphify_command=args.graphify_command,
        )
    except (FileNotFoundError, GraphifyCliError, NotADirectoryError, ValueError) as exc:
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


def _validate_rim(args: argparse.Namespace) -> int:
    try:
        result = validate_rim_json(args.rim_json)
    except FileNotFoundError as exc:
        print(f"rilde: {exc}", file=sys.stderr)
        return 1

    print("RIM validation passed." if result.valid else "RIM validation failed.")
    print(f"Schema version: {result.schema_version or 'unknown'}")
    print(f"Nodes: {result.node_count}")
    print(f"Edges: {result.edge_count}")
    print(f"Findings: {result.finding_count}")
    print(f"Errors: {result.error_count}")
    print(f"Warnings: {result.warning_count}")

    for issue in result.issues:
        location = f" at {issue.location}" if issue.location else ""
        print(f"[{issue.severity.value}] {issue.code}{location}: {issue.message}")

    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
