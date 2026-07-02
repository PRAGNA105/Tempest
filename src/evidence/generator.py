from __future__ import annotations

import hashlib
from typing import Any

from detection.models import LeakFinding
from evidence.models import EvidenceFact, EvidenceNode, EvidenceRecord
from rim.models import RepositoryIntelligenceModel, RepositoryNode


def generate_evidence(
    rim: RepositoryIntelligenceModel,
    findings: list[LeakFinding],
) -> list[EvidenceRecord]:
    nodes_by_id = {node.id: node for node in rim.nodes}
    return [_evidence_record(finding, nodes_by_id) for finding in findings]


def _evidence_record(
    finding: LeakFinding,
    nodes_by_id: dict[str, RepositoryNode],
) -> EvidenceRecord:
    primary_node = nodes_by_id.get(finding.source_node_id)
    related_nodes, missing_node_ids = _related_nodes(finding, nodes_by_id)

    return EvidenceRecord(
        id=_evidence_id(finding.id),
        leak_finding_id=finding.id,
        policy_id=finding.policy_id,
        title=finding.title,
        severity=finding.severity,
        summary=finding.evidence,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        confidence=finding.confidence,
        primary_node=_evidence_node(primary_node) if primary_node else None,
        related_nodes=related_nodes,
        facts=_evidence_facts(finding, primary_node, related_nodes),
        metadata={
            "generator": "deterministic_evidence_generator",
            "missing_node_ids": missing_node_ids,
        },
    )


def _related_nodes(
    finding: LeakFinding,
    nodes_by_id: dict[str, RepositoryNode],
) -> tuple[list[EvidenceNode], list[str]]:
    related: list[EvidenceNode] = []
    missing: list[str] = []
    seen: set[str] = set()

    for node_id in finding.related_node_ids:
        if node_id == finding.source_node_id or node_id in seen:
            continue
        seen.add(node_id)
        node = nodes_by_id.get(node_id)
        if node is None:
            missing.append(node_id)
            continue
        related.append(_evidence_node(node))

    return related, missing


def _evidence_node(node: RepositoryNode) -> EvidenceNode:
    return EvidenceNode(
        id=node.id,
        label=node.label,
        kind=node.kind.value,
        source_file=node.source_file,
        confidence=node.confidence,
        metadata=_selected_node_metadata(node),
    )


def _selected_node_metadata(node: RepositoryNode) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for key in (
        "secret_type",
        "fingerprint",
        "resource_type",
        "annotation_type",
        "candidate",
        "annotations",
    ):
        if key in node.metadata:
            selected[key] = node.metadata[key]
    return selected


def _evidence_facts(
    finding: LeakFinding,
    primary_node: RepositoryNode | None,
    related_nodes: list[EvidenceNode],
) -> list[EvidenceFact]:
    facts = [
        EvidenceFact(key="policy_id", value=finding.policy_id),
        EvidenceFact(key="severity", value=finding.severity.value),
        EvidenceFact(key="confidence", value=finding.confidence),
    ]

    for key, value in sorted(finding.metadata.items()):
        facts.append(EvidenceFact(key=key, value=value, source_node_id=finding.source_node_id))

    if primary_node is not None:
        facts.append(
            EvidenceFact(
                key="primary_node_kind",
                value=primary_node.kind.value,
                source_node_id=primary_node.id,
            )
        )

    for node in related_nodes:
        facts.append(
            EvidenceFact(
                key=f"related_node:{node.kind}",
                value=node.label,
                source_node_id=node.id,
            )
        )

    return facts


def _evidence_id(leak_finding_id: str) -> str:
    digest = hashlib.sha256(f"evidence:{leak_finding_id}".encode()).hexdigest()
    return f"evidence-{digest[:16]}"
