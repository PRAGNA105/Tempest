from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from rim.models import RepositoryIntelligenceModel, RIMEdgeType

SUPPORTED_SCHEMA_VERSION = "0.1"


class RimValidationSeverity(str, Enum):  # noqa: UP042 - Python 3.10 test runtime lacks StrEnum.
    ERROR = "error"
    WARNING = "warning"


class RimValidationIssue(BaseModel):
    severity: RimValidationSeverity
    code: str
    message: str
    location: str | None = None


class RimValidationResult(BaseModel):
    valid: bool
    schema_version: str | None = None
    node_count: int = 0
    edge_count: int = 0
    finding_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    issues: list[RimValidationIssue] = Field(default_factory=list)


def validate_rim_json(path: Path) -> RimValidationResult:
    if not path.exists():
        raise FileNotFoundError(f"RIM JSON not found: {path}")

    try:
        rim = RepositoryIntelligenceModel.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        return _result(
            None,
            [
                RimValidationIssue(
                    severity=RimValidationSeverity.ERROR,
                    code="schema_validation_failed",
                    message=_validation_error_message(exc),
                    location="rim",
                )
            ],
        )

    return validate_rim(rim)


def validate_rim(rim: RepositoryIntelligenceModel) -> RimValidationResult:
    issues: list[RimValidationIssue] = []
    node_ids = _node_ids(rim, issues)
    source_files = {node.source_file for node in rim.nodes if node.source_file}

    if rim.schema_version != SUPPORTED_SCHEMA_VERSION:
        issues.append(
            RimValidationIssue(
                severity=RimValidationSeverity.ERROR,
                code="unsupported_schema_version",
                message=(
                    f"Unsupported RIM schema version {rim.schema_version!r}; "
                    f"expected {SUPPORTED_SCHEMA_VERSION!r}."
                ),
                location="schema_version",
            )
        )

    _validate_edges(rim, node_ids, source_files, issues)
    return _result(rim, issues)


def _node_ids(
    rim: RepositoryIntelligenceModel,
    issues: list[RimValidationIssue],
) -> set[str]:
    node_ids: set[str] = set()
    seen: set[str] = set()

    for index, node in enumerate(rim.nodes):
        location = f"nodes[{index}]"
        if not node.id.strip():
            issues.append(
                RimValidationIssue(
                    severity=RimValidationSeverity.ERROR,
                    code="empty_node_id",
                    message="Node ID cannot be empty.",
                    location=location,
                )
            )
            continue

        if node.id in seen:
            issues.append(
                RimValidationIssue(
                    severity=RimValidationSeverity.ERROR,
                    code="duplicate_node_id",
                    message=f"Duplicate node ID: {node.id}",
                    location=location,
                )
            )
        seen.add(node.id)
        node_ids.add(node.id)

    return node_ids


def _validate_edges(
    rim: RepositoryIntelligenceModel,
    node_ids: set[str],
    source_files: set[str],
    issues: list[RimValidationIssue],
) -> None:
    seen_edges: set[tuple[str, str, str]] = set()

    for index, edge in enumerate(rim.edges):
        location = f"edges[{index}]"
        edge_key = (edge.source, edge.target, _edge_type_value(edge.type))
        if edge_key in seen_edges:
            issues.append(
                RimValidationIssue(
                    severity=RimValidationSeverity.ERROR,
                    code="duplicate_edge",
                    message=(
                        "Duplicate edge: "
                        f"{edge.source} -> {edge.target} ({_edge_type_value(edge.type)})"
                    ),
                    location=location,
                )
            )
        seen_edges.add(edge_key)

        _validate_endpoint(edge.source, "source", node_ids, source_files, location, issues)
        _validate_endpoint(edge.target, "target", node_ids, source_files, location, issues)


def _validate_endpoint(
    value: str,
    role: str,
    node_ids: set[str],
    source_files: set[str],
    location: str,
    issues: list[RimValidationIssue],
) -> None:
    if value in node_ids:
        return

    if value in source_files:
        issues.append(
            RimValidationIssue(
                severity=RimValidationSeverity.WARNING,
                code="edge_endpoint_uses_source_file",
                message=f"Edge {role} {value!r} resolves by source_file, not node ID.",
                location=location,
            )
        )
        return

    issues.append(
        RimValidationIssue(
            severity=RimValidationSeverity.ERROR,
            code="missing_edge_endpoint",
            message=f"Edge {role} {value!r} does not resolve to a RIM node.",
            location=location,
        )
    )


def _result(
    rim: RepositoryIntelligenceModel | None,
    issues: list[RimValidationIssue],
) -> RimValidationResult:
    error_count = sum(1 for issue in issues if issue.severity == RimValidationSeverity.ERROR)
    warning_count = sum(1 for issue in issues if issue.severity == RimValidationSeverity.WARNING)
    return RimValidationResult(
        valid=error_count == 0,
        schema_version=rim.schema_version if rim else None,
        node_count=len(rim.nodes) if rim else 0,
        edge_count=len(rim.edges) if rim else 0,
        finding_count=len(rim.findings) if rim else 0,
        error_count=error_count,
        warning_count=warning_count,
        issues=issues,
    )


def _validation_error_message(exc: ValidationError) -> str:
    first_error = exc.errors()[0] if exc.errors() else None
    if not first_error:
        return str(exc)
    location = ".".join(str(part) for part in first_error.get("loc", ()))
    message = str(first_error.get("msg", "RIM schema validation failed."))
    if location:
        return f"{location}: {message}"
    return message


def _edge_type_value(edge_type: RIMEdgeType | str) -> str:
    if isinstance(edge_type, RIMEdgeType):
        return edge_type.value
    return edge_type
