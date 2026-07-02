from __future__ import annotations

from pathlib import PurePath

from annotation.models import AnnotatedNode, AnnotationType
from boundary.models import ProductionBoundaryCandidate
from environment.models import EnvironmentCandidate
from rim.models import (
    EnvironmentNode,
    ProductionBoundaryNode,
    RepositoryIntelligenceModel,
    RepositoryNode,
    RIMEdge,
    RIMEdgeType,
    RIMNodeKind,
)


def annotate_rim(
    rim: RepositoryIntelligenceModel,
    environment_candidates: list[EnvironmentCandidate] | None = None,
    boundary_candidates: list[ProductionBoundaryCandidate] | None = None,
) -> RepositoryIntelligenceModel:
    """Return a RIM enriched with environment and production boundary annotations."""
    annotated = rim.model_copy(deep=True)
    environments = environment_candidates or []
    boundaries = boundary_candidates or []

    nodes_by_id = {node.id: node for node in annotated.nodes}
    edge_keys = {
        (edge.source, edge.target, _edge_type_value(edge.type)) for edge in annotated.edges
    }

    for candidate in environments:
        target = _source_node_for_candidate(
            nodes_by_id,
            candidate.source_file,
            candidate.source_finding_id,
        )
        environment_node = _environment_node(candidate)
        _add_node(annotated, nodes_by_id, environment_node)

        if target is not None:
            annotation = _environment_annotation(candidate, target.id)
            _enrich_node(target, annotation)
            _add_edge(
                annotated,
                edge_keys,
                RIMEdge(
                    source=target.id,
                    target=environment_node.id,
                    type=RIMEdgeType.BELONGS_TO_ENVIRONMENT,
                    confidence=candidate.confidence,
                    metadata={
                        "annotation_id": annotation.id,
                        "environment_candidate_id": candidate.id,
                        "source_finding_id": candidate.source_finding_id,
                    },
                ),
            )

    for candidate in boundaries:
        target = _source_node_for_candidate(
            nodes_by_id,
            candidate.source_file,
            candidate.source_finding_id,
        )
        boundary_node = _boundary_node(candidate)
        _add_node(annotated, nodes_by_id, boundary_node)

        if target is not None:
            annotation = _boundary_annotation(candidate, target.id)
            _enrich_node(target, annotation)
            _add_edge(
                annotated,
                edge_keys,
                RIMEdge(
                    source=target.id,
                    target=boundary_node.id,
                    type=RIMEdgeType.CROSSES_BOUNDARY,
                    confidence=candidate.confidence,
                    metadata={
                        "annotation_id": annotation.id,
                        "boundary_candidate_id": candidate.id,
                        "source_environment_id": candidate.source_environment_id,
                        "source_finding_id": candidate.source_finding_id,
                    },
                ),
            )

    annotated.metadata["annotation"] = {
        "environment_candidate_count": len(environments),
        "boundary_candidate_count": len(boundaries),
    }
    return annotated


def _add_node(
    rim: RepositoryIntelligenceModel,
    nodes_by_id: dict[str, RepositoryNode],
    node: RepositoryNode,
) -> None:
    if node.id in nodes_by_id:
        return
    rim.nodes.append(node)
    nodes_by_id[node.id] = node


def _add_edge(
    rim: RepositoryIntelligenceModel,
    edge_keys: set[tuple[str, str, str]],
    edge: RIMEdge,
) -> None:
    key = (edge.source, edge.target, _edge_type_value(edge.type))
    if key in edge_keys:
        return
    rim.edges.append(edge)
    edge_keys.add(key)


def _environment_node(candidate: EnvironmentCandidate) -> EnvironmentNode:
    return EnvironmentNode(
        id=_environment_node_id(candidate.id),
        label=candidate.name.value,
        source_file=candidate.source_file,
        confidence=candidate.confidence,
        metadata={
            "annotation_type": AnnotationType.ENVIRONMENT.value,
            "candidate": candidate.model_dump(mode="json"),
        },
    )


def _boundary_node(candidate: ProductionBoundaryCandidate) -> ProductionBoundaryNode:
    return ProductionBoundaryNode(
        id=_boundary_node_id(candidate.id),
        label=candidate.boundary_type.value,
        source_file=candidate.source_file,
        confidence=candidate.confidence,
        metadata={
            "annotation_type": AnnotationType.PRODUCTION_BOUNDARY.value,
            "candidate": candidate.model_dump(mode="json"),
        },
    )


def _environment_annotation(candidate: EnvironmentCandidate, target_node_id: str) -> AnnotatedNode:
    return AnnotatedNode(
        id=f"annotation:environment:{candidate.id}:{target_node_id}",
        target_node_id=target_node_id,
        annotation_type=AnnotationType.ENVIRONMENT,
        source_candidate_id=candidate.id,
        source_finding_id=candidate.source_finding_id,
        confidence=candidate.confidence,
        metadata={
            "environment": candidate.name.value,
            "source_file": candidate.source_file,
            "line": candidate.line,
            "column": candidate.column,
        },
    )


def _boundary_annotation(
    candidate: ProductionBoundaryCandidate,
    target_node_id: str,
) -> AnnotatedNode:
    return AnnotatedNode(
        id=f"annotation:boundary:{candidate.id}:{target_node_id}",
        target_node_id=target_node_id,
        annotation_type=AnnotationType.PRODUCTION_BOUNDARY,
        source_candidate_id=candidate.id,
        source_finding_id=candidate.source_finding_id,
        confidence=candidate.confidence,
        metadata={
            "boundary_type": candidate.boundary_type.value,
            "externally_reachable": candidate.externally_reachable,
            "source_environment_id": candidate.source_environment_id,
            "source_file": candidate.source_file,
            "line": candidate.line,
            "column": candidate.column,
        },
    )


def _enrich_node(node: RepositoryNode, annotation: AnnotatedNode) -> None:
    annotations = node.metadata.setdefault("annotations", [])
    payload = annotation.model_dump(mode="json")
    if payload not in annotations:
        annotations.append(payload)


def _source_node_for_candidate(
    nodes_by_id: dict[str, RepositoryNode],
    source_file: str,
    source_finding_id: str,
) -> RepositoryNode | None:
    source_file_candidates = _source_file_candidates(source_file)
    for node in nodes_by_id.values():
        if node.kind != RIMNodeKind.FILE:
            continue
        if node.id in source_file_candidates or node.source_file in source_file_candidates:
            return node
        if _same_path(node.label, source_file) or _same_path(node.source_file, source_file):
            return node

    return nodes_by_id.get(f"finding:{source_finding_id}")


def _source_file_candidates(source_file: str) -> set[str]:
    normalized = source_file.replace("\\", "/")
    return {
        source_file,
        normalized,
        f"file:{source_file}",
        f"file:{normalized}",
    }


def _same_path(value: str | None, source_file: str) -> bool:
    if not value:
        return False
    return PurePath(value.replace("\\", "/")).as_posix() == PurePath(
        source_file.replace("\\", "/")
    ).as_posix()


def _environment_node_id(candidate_id: str) -> str:
    return f"environment:{candidate_id}"


def _boundary_node_id(candidate_id: str) -> str:
    return f"boundary:{candidate_id}"


def _edge_type_value(edge_type: RIMEdgeType | str) -> str:
    if isinstance(edge_type, RIMEdgeType):
        return edge_type.value
    return edge_type
