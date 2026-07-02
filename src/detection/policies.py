from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import PurePath
from typing import Any

from detection.models import LeakFinding, LeakSeverity
from rim.models import (
    RepositoryIntelligenceModel,
    RepositoryNode,
    RIMEdge,
    RIMEdgeType,
    RIMNodeKind,
)


class ProductionSecretBoundaryPolicy:
    """Detect secrets in files that cross externally reachable production boundaries."""

    id = "production_secret_boundary"
    name = "Secret in externally reachable production boundary"

    def detect(self, rim: RepositoryIntelligenceModel) -> list[LeakFinding]:
        nodes_by_id = {node.id: node for node in rim.nodes}
        boundaries_by_file = _external_boundaries_by_file(rim.edges, nodes_by_id)
        findings: list[LeakFinding] = []
        seen: set[str] = set()

        for node in rim.nodes:
            if node.kind != RIMNodeKind.SECRET:
                continue

            source_file = _normalized_path(node.source_file)
            if source_file is None:
                continue

            for edge, boundary in boundaries_by_file.get(source_file, []):
                finding_id = _finding_id(self.id, node.id, boundary.id)
                if finding_id in seen:
                    continue
                seen.add(finding_id)
                findings.append(_leak_finding(self.id, node, edge, boundary, finding_id))

        return findings


def _external_boundaries_by_file(
    edges: list[RIMEdge],
    nodes_by_id: dict[str, RepositoryNode],
) -> dict[str, list[tuple[RIMEdge, RepositoryNode]]]:
    boundaries_by_file: dict[str, list[tuple[RIMEdge, RepositoryNode]]] = defaultdict(list)

    for edge in edges:
        if _edge_type_value(edge.type) != RIMEdgeType.CROSSES_BOUNDARY.value:
            continue

        boundary = nodes_by_id.get(edge.target)
        if boundary is None or boundary.kind != RIMNodeKind.PRODUCTION_BOUNDARY:
            continue
        if not _is_externally_reachable(boundary):
            continue

        source_file = _normalized_path(boundary.source_file)
        if source_file is None:
            source_node = nodes_by_id.get(edge.source) if edge.source else None
            source_file = _normalized_path(source_node.source_file if source_node else None)
        if source_file is None:
            continue

        boundaries_by_file[source_file].append((edge, boundary))

    return boundaries_by_file


def _leak_finding(
    policy_id: str,
    secret: RepositoryNode,
    edge: RIMEdge,
    boundary: RepositoryNode,
    finding_id: str,
) -> LeakFinding:
    secret_metadata = secret.metadata
    boundary_candidate = _candidate_metadata(boundary)
    boundary_type = str(boundary_candidate.get("boundary_type") or boundary.label)
    secret_type = str(secret_metadata.get("secret_type") or secret.label)
    source_file = secret.source_file

    return LeakFinding(
        id=finding_id,
        policy_id=policy_id,
        title="Secret in externally reachable production boundary",
        severity=_severity(secret, boundary),
        source_node_id=secret.id,
        source_file=source_file,
        line=_optional_int(secret_metadata.get("line")),
        column=_optional_int(secret_metadata.get("column")),
        confidence=_combined_confidence(secret.confidence, boundary.confidence),
        evidence=(
            f"{secret_type} in {source_file or 'unknown source'} is colocated with "
            f"externally reachable production boundary {boundary_type}."
        ),
        related_node_ids=[edge.source, boundary.id],
        metadata={
            "policy": policy_id,
            "secret_type": secret_type,
            "boundary_type": boundary_type,
            "boundary_node_id": boundary.id,
            "boundary_source_node_id": edge.source,
            "externally_reachable": True,
        },
    )


def _candidate_metadata(node: RepositoryNode) -> dict[str, Any]:
    candidate = node.metadata.get("candidate")
    if isinstance(candidate, dict):
        return candidate
    return {}


def _is_externally_reachable(node: RepositoryNode) -> bool:
    candidate = _candidate_metadata(node)
    return candidate.get("externally_reachable") is True


def _severity(secret: RepositoryNode, boundary: RepositoryNode) -> LeakSeverity:
    if secret.confidence >= 0.9 and boundary.confidence >= 0.8:
        return LeakSeverity.CRITICAL
    return LeakSeverity.HIGH


def _combined_confidence(secret_confidence: float, boundary_confidence: float) -> float:
    return round(min(secret_confidence, boundary_confidence), 3)


def _optional_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _normalized_path(value: str | None) -> str | None:
    if not value:
        return None
    return PurePath(value.replace("\\", "/")).as_posix()


def _edge_type_value(edge_type: RIMEdgeType | str) -> str:
    if isinstance(edge_type, RIMEdgeType):
        return edge_type.value
    return edge_type


def _finding_id(policy_id: str, secret_node_id: str, boundary_node_id: str) -> str:
    digest = hashlib.sha256(
        f"{policy_id}:{secret_node_id}:{boundary_node_id}".encode()
    ).hexdigest()
    return f"leak-{digest[:16]}"
