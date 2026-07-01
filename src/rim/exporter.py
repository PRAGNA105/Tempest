from __future__ import annotations

from pathlib import Path

from graph import Edge, Node, RepositoryGraph
from rim.models import (
    ClassNode,
    CloudResourceNode,
    DatabaseNode,
    FileNode,
    FunctionNode,
    ProductionBoundaryNode,
    RIMEdge,
    RIMEdgeType,
    RIMNodeKind,
    RepositoryIntelligenceModel,
    RepositoryNode,
    SecretNode,
    URLNode,
)
from scanners import CloudResourceFinding, DatabaseFinding, Finding, SecretFinding, URLFinding


GRAPH_TYPE_TO_RIM_KIND = {
    "repository": RIMNodeKind.REPOSITORY,
    "file": RIMNodeKind.FILE,
    "function": RIMNodeKind.FUNCTION,
    "class": RIMNodeKind.CLASS,
}

GRAPH_RELATION_TO_RIM_EDGE = {
    "contains": RIMEdgeType.CONTAINS,
    "imports": RIMEdgeType.IMPORTS,
    "calls": RIMEdgeType.CALLS,
    "references": RIMEdgeType.REFERENCES,
    "defines": RIMEdgeType.DEFINES,
}


def build_rim(
    graph: RepositoryGraph,
    findings: list[Finding] | None = None,
    *,
    metadata: dict[str, object] | None = None,
) -> RepositoryIntelligenceModel:
    scanner_findings = findings or []
    nodes = [_graph_node_to_rim_node(node) for node in graph.nodes]
    nodes.extend(_finding_to_rim_node(finding) for finding in scanner_findings)

    edges = [_graph_edge_to_rim_edge(edge) for edge in graph.edges]
    edges.extend(_finding_edge(finding) for finding in scanner_findings)

    return RepositoryIntelligenceModel(
        nodes=nodes,
        edges=edges,
        findings=scanner_findings,
        metadata={
            "graph_metadata": graph.metadata,
            **(metadata or {}),
        },
    )


def export_rim_json(rim: RepositoryIntelligenceModel, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rim.model_dump_json(indent=2), encoding="utf-8")
    return output_path


def _graph_node_to_rim_node(node: Node) -> RepositoryNode:
    kind = GRAPH_TYPE_TO_RIM_KIND.get(node.type, RIMNodeKind.REPOSITORY)
    model = {
        RIMNodeKind.FILE: FileNode,
        RIMNodeKind.FUNCTION: FunctionNode,
        RIMNodeKind.CLASS: ClassNode,
    }.get(kind, RepositoryNode)
    return model(
        id=node.id,
        label=node.label,
        kind=kind,
        source_id=node.id,
        source_file=node.source_file,
        metadata={"graph_type": node.type, **node.metadata},
    )


def _graph_edge_to_rim_edge(edge: Edge) -> RIMEdge:
    return RIMEdge(
        source=edge.source,
        target=edge.target,
        type=GRAPH_RELATION_TO_RIM_EDGE.get(edge.relation, edge.relation),
        confidence=edge.confidence,
        metadata={"graph_relation": edge.relation, "source_file": edge.source_file, **edge.metadata},
    )


def _finding_to_rim_node(finding: Finding) -> RepositoryNode:
    if isinstance(finding, SecretFinding):
        return SecretNode(
            id=f"finding:{finding.id}",
            label=finding.secret_type,
            source_file=finding.source_file,
            confidence=finding.confidence,
            metadata=finding.model_dump(mode="json"),
        )
    if isinstance(finding, URLFinding):
        return URLNode(
            id=f"finding:{finding.id}",
            label=finding.hostname or finding.url,
            source_file=finding.source_file,
            confidence=finding.confidence,
            metadata=finding.model_dump(mode="json"),
        )
    if isinstance(finding, DatabaseFinding):
        return DatabaseNode(
            id=f"finding:{finding.id}",
            label=finding.database_name or finding.host or finding.database_type,
            source_file=finding.source_file,
            confidence=finding.confidence,
            metadata=finding.model_dump(mode="json"),
        )
    if isinstance(finding, CloudResourceFinding):
        return CloudResourceNode(
            id=f"finding:{finding.id}",
            label=finding.resource_id,
            source_file=finding.source_file,
            confidence=finding.confidence,
            metadata=finding.model_dump(mode="json"),
        )
    return ProductionBoundaryNode(
        id=f"finding:{finding.id}",
        label=finding.value,
        source_file=finding.source_file,
        confidence=finding.confidence,
        metadata=finding.model_dump(mode="json"),
    )


def _finding_edge(finding: Finding) -> RIMEdge:
    return RIMEdge(
        source=finding.source_file,
        target=f"finding:{finding.id}",
        type=RIMEdgeType.ANNOTATES,
        confidence=finding.confidence,
        metadata={"finding_id": finding.id},
    )
