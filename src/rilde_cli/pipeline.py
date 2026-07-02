from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from annotation import annotate_rim
from boundary import ProductionBoundaryDiscovery, save_boundary_candidates_json
from detection import ProductionSecretBoundaryPolicy, save_leak_findings_json
from environment import EnvironmentDiscovery, save_environment_candidates_json
from evidence import generate_evidence, save_evidence_json
from graphify_adapter import GraphifyJsonAdapter, run_graphify_cli
from reports import generate_report, save_report_json, save_report_markdown
from rim import build_rim, export_rim_json
from scanners import (
    CloudResourceScanner,
    DatabaseScanner,
    Finding,
    SecretScanner,
    URLScanner,
    save_findings_json,
)


@dataclass(frozen=True)
class PipelineResult:
    paths: dict[str, Path]
    counts: dict[str, int]


def run_deterministic_pipeline(
    repository_path: Path,
    *,
    output_dir: Path = Path("state"),
    graph_json: Path | None = None,
    graphify_command: list[str] | None = None,
) -> PipelineResult:
    repository = repository_path.resolve()
    if not repository.exists():
        raise FileNotFoundError(f"Repository path not found: {repository_path}")
    if not repository.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repository_path}")

    output_root = output_dir
    output_root.mkdir(parents=True, exist_ok=True)

    if graphify_command is not None:
        run_graphify_cli(repository, graphify_command, graph_json=graph_json)

    graph = GraphifyJsonAdapter(graph_json).build_graph(repository)

    url_findings = URLScanner().scan(repository)
    secret_findings = SecretScanner().scan(repository)
    database_findings = DatabaseScanner().scan(repository)
    cloud_findings = CloudResourceScanner().scan(repository)
    findings: list[Finding] = [
        *url_findings,
        *secret_findings,
        *database_findings,
        *cloud_findings,
    ]

    environment_candidates = EnvironmentDiscovery().discover(findings)
    boundary_candidates = ProductionBoundaryDiscovery().discover(
        environment_candidates,
        findings,
    )
    rim = build_rim(
        graph,
        findings,
        metadata={
            "pipeline": "deterministic_cli",
            "repository_path": str(repository),
        },
    )
    annotated_rim = annotate_rim(rim, environment_candidates, boundary_candidates)
    leak_findings = ProductionSecretBoundaryPolicy().detect(annotated_rim)
    evidence_records = generate_evidence(annotated_rim, leak_findings)
    report = generate_report(evidence_records)

    paths = _artifact_paths(output_root)
    save_findings_json(url_findings, paths["url_findings"])
    save_findings_json(secret_findings, paths["secret_findings"])
    save_findings_json(database_findings, paths["database_findings"])
    save_findings_json(cloud_findings, paths["cloud_findings"])
    save_environment_candidates_json(environment_candidates, paths["environment_candidates"])
    save_boundary_candidates_json(boundary_candidates, paths["boundary_candidates"])
    export_rim_json(annotated_rim, paths["rim"])
    save_leak_findings_json(leak_findings, paths["leak_findings"])
    save_evidence_json(evidence_records, paths["evidence"])
    save_report_json(report, paths["report_json"])
    save_report_markdown(report, paths["report_markdown"])

    return PipelineResult(
        paths=paths,
        counts={
            "graph_nodes": len(graph.nodes),
            "graph_edges": len(graph.edges),
            "url_findings": len(url_findings),
            "secret_findings": len(secret_findings),
            "database_findings": len(database_findings),
            "cloud_findings": len(cloud_findings),
            "scanner_findings": len(findings),
            "environment_candidates": len(environment_candidates),
            "boundary_candidates": len(boundary_candidates),
            "rim_nodes": len(annotated_rim.nodes),
            "rim_edges": len(annotated_rim.edges),
            "leak_findings": len(leak_findings),
            "evidence_records": len(evidence_records),
            "report_findings": len(report.findings),
        },
    )


def _artifact_paths(output_dir: Path) -> dict[str, Path]:
    return {
        "url_findings": output_dir / "url_findings.json",
        "secret_findings": output_dir / "secret_findings.json",
        "database_findings": output_dir / "database_findings.json",
        "cloud_findings": output_dir / "cloud_findings.json",
        "environment_candidates": output_dir / "environment_candidates.json",
        "boundary_candidates": output_dir / "boundary_candidates.json",
        "rim": output_dir / "rim.json",
        "leak_findings": output_dir / "leak_findings.json",
        "evidence": output_dir / "evidence_records.json",
        "report_json": output_dir / "reports" / "report.json",
        "report_markdown": output_dir / "reports" / "report.md",
    }
