#!/usr/bin/env python3
"""Demo script: Run semantic_trace on multiple test projects and display results.

This script demonstrates the semantic trace leak detection engine across:
  - clean_app: A safe project with no violations (baseline)
  - test_app: A vulnerable project with P12, P13, P14 violations
  - demo_app: A comprehensive unsafe project with all 5 policy violations

Usage:
    python demo_scanner.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

from semantic_trace.brain import orchestrator


PROJECTS = {
    "clean_app": {
        "desc": "✓ Safe baseline — no violations expected",
        "color": "green",
    },
    "test_app": {
        "desc": "⚠ Vulnerable — P12 (chains), P13 (constructed), P14 (aliases)",
        "color": "yellow",
    },
    "demo_app": {
        "desc": "⚠⚠ Unsafe — All 5 policies (P10-P14)",
        "color": "red",
    },
}


def format_finding(f) -> str:
    """Format a single finding as a compact one-liner."""
    loc = f"{f.file}:{f.lineno}" if f.lineno else f.file
    evidence_str = ""
    if f.evidence:
        # Show only the first evidence item, truncated to 50 chars
        ev = f.evidence[0][:50]
        if len(f.evidence[0]) > 50:
            ev += "..."
        evidence_str = f" | {ev}"
    return f"  [{f.policy_id}] {loc:30} | {f.severity.upper():6} {f.confidence:>3.0%}{evidence_str}"


def run_demo():
    """Run semantic trace on all demo projects."""
    root = Path(__file__).parent.resolve()
    
    print("\n" + "=" * 80)
    print("SEMANTIC TRACE DEMO — Multi-Project Vulnerability Scanner")
    print("=" * 80)
    
    all_findings = {}
    total_findings = 0
    
    for project_name, project_info in PROJECTS.items():
        project_path = root / project_name
        if not project_path.is_dir():
            print(f"\n⊘ {project_name}: NOT FOUND at {project_path}")
            continue
        
        print(f"\n{'-' * 80}")
        print(f"PROJECT: {project_name}")
        print(f"Description: {project_info['desc']}")
        print(f"Path: {project_path}")
        print(f"{'-' * 80}")
        
        # Run the scanner
        result = orchestrator.run("", project_path)
        all_findings[project_name] = result.findings
        total_findings += len(result.findings)
        
        # Display summary
        if not result.findings:
            print("\n✓ [OK] No violations detected. Project appears clean.")
        else:
            by_policy = defaultdict(int)
            by_severity = defaultdict(int)
            for f in result.findings:
                by_policy[f.policy_id] += 1
                by_severity[f.severity] += 1
            
            print(f"\n✗ [FINDINGS] {len(result.findings)} violation(s) detected")
            print(f"  Policies: {', '.join(f'{p}:{by_policy[p]}' for p in sorted(by_policy.keys()))}")
            print(f"  Severity: {', '.join(f'{s.upper()}:{by_severity[s]}' for s in sorted(by_severity.keys()))}")
            
            # Group by policy
            by_policy_findings = defaultdict(list)
            for f in result.findings:
                by_policy_findings[f.policy_id].append(f)
            
            for policy_id in sorted(by_policy_findings.keys()):
                findings = by_policy_findings[policy_id]
                print(f"\n  {policy_id} ({len(findings)} finding{'s' if len(findings) != 1 else ''}):")
                for f in findings:
                    print(format_finding(f))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nProjects scanned: {len(all_findings)}")
    print(f"Total findings: {total_findings}")
    
    for project_name, findings in all_findings.items():
        status = "✓ CLEAN" if not findings else f"✗ {len(findings)} ISSUES"
        print(f"  {project_name:15} → {status}")
    
    # Export JSON for further processing
    json_output = {
        "timestamp": Path(__file__).stat().st_mtime,
        "projects": {
            name: [
                {
                    "id": f.id,
                    "policy": f.policy_id,
                    "severity": f.severity,
                    "title": f.title,
                    "file": f.file,
                    "lineno": f.lineno,
                }
                for f in findings
            ]
            for name, findings in all_findings.items()
        },
    }
    
    json_path = root / "demo_results.json"
    json_path.write_text(json.dumps(json_output, indent=2), encoding="utf-8")
    print(f"\nJSON report: {json_path}")
    
    print("\n" + "=" * 80)
    print("Demo complete. Use these findings to understand policy violations.")
    print("=" * 80 + "\n")
    
    return 0 if total_findings > 0 else 1  # Return non-zero if issues found


if __name__ == "__main__":
    sys.exit(run_demo())
