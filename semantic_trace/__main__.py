"""Minimal local runner for the semantic trace Graph Engine.

Drives the scripted SemanticTraceAgent (brain/orchestrator.py) over a target
project, prints the Goal/Thought/Tool/Observation/Decision trace, then the
findings (P10-P14) with explanations, and finally a JSON dump.

Usage:
    python -m semantic_trace <target_dir> [--json-only]

Example:
    python -m semantic_trace demo_app
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Force UTF-8 on Windows so the arrow glyphs in chains print correctly.
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

from semantic_trace.brain import orchestrator
from semantic_trace.core.constants import POLICY_P12
from semantic_trace.core.policy_config import load_policy_config


def _format_finding(f) -> dict:
    """Serialise a Finding to a plain dict for JSON output."""
    return {
        "id": f.id,
        "policy_id": f.policy_id,
        "severity": f.severity,
        "title": f.title,
        "file": f.file,
        "lineno": f.lineno,
        "source_node": f.source_node,
        "sink_node": f.sink_node,
        "path": f.path,
        "evidence": f.evidence,
        "explanation": f.explanation,
        "confidence": f.confidence,
    }


def main(
    target: str,
    json_only: bool = False,
    use_llm: bool = False,
    policy_config_path: str | None = None,
) -> None:
    root = Path(target).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    policy_config = None
    if policy_config_path:
        policy_config = load_policy_config(policy_config_path)

    result = orchestrator.run(
        "",
        root,
        policy_config=policy_config,
        use_llm=use_llm,
    )

    if json_only:
        print(json.dumps({
            "goal": result.goal,
            "root": result.root,
            "summary": result.summary,
            "findings": [_format_finding(f) for f in result.findings],
        }, indent=2))
        return

    # --- Agent trace ------------------------------------------------------
    print(f"[semantic_trace] SemanticTraceAgent on: {root}\n")
    print("=" * 64)
    print("AGENT TRACE")
    print("=" * 64)
    for step in result.trace:
        print(f"\n{step.phase}:")
        for line in step.text.splitlines():
            print(f"    {line}")

    # --- Findings ---------------------------------------------------------
    print("\n" + "=" * 64)
    print("FINDINGS")
    print("=" * 64)

    if not result.findings:
        print("\n[OK] No policy violations detected. Target appears clean.")
        return

    print(f"\n[!!] {result.summary}\n")
    _print_ranked_findings(result.findings)
    print("-" * 64)

    # --- JSON -------------------------------------------------------------
    print("\n[JSON output]\n")
    print(json.dumps([_format_finding(f) for f in result.findings], indent=2))


def _print_ranked_findings(findings) -> None:
    """Print ranked findings, grouping P12 chains by shared sink."""
    p12_by_sink = defaultdict(list)
    for finding in findings:
        if finding.policy_id == POLICY_P12:
            p12_by_sink[finding.sink_node].append(finding)

    printed_p12_sinks = set()
    for finding in findings:
        if finding.policy_id != POLICY_P12:
            _print_one_finding(finding)
            continue

        sink = finding.sink_node
        if sink in printed_p12_sinks:
            continue
        printed_p12_sinks.add(sink)
        print("-" * 64)
        print(f"  [P12] Import chains to production sink: {sink}")
        print(f"  Chains: {len(p12_by_sink[sink])}")
        for grouped in p12_by_sink[sink]:
            _print_one_finding(grouped, compact=True)


def _print_one_finding(f, compact: bool = False) -> None:
    if not compact:
        print("-" * 64)
    print(f"  [{f.policy_id}] {f.title}")
    print(f"  Severity: {f.severity} | Confidence: {f.confidence}")
    if f.file:
        loc = f"{f.file}:{f.lineno}" if f.lineno else f.file
        print(f"  Location: {loc}")
    for ev in f.evidence:
        print(f"    * {ev}")
    print(f"  Explanation: {f.explanation}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m semantic_trace",
        description="Run the local Semantic Trace Graph Engine.",
    )
    parser.add_argument("target_dir")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--use-llm", action="store_true")
    parser.add_argument(
        "--policy-config",
        help="Path to a JSON policy config that extends or replaces patterns.",
    )
    ns = parser.parse_args()
    main(
        ns.target_dir,
        json_only=ns.json_only,
        use_llm=ns.use_llm,
        policy_config_path=ns.policy_config,
    )
