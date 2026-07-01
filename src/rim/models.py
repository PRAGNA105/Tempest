from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

from scanners import Finding


class RIMNodeKind(str, Enum):
    REPOSITORY = "repository"
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    SECRET = "secret"
    URL = "url"
    DATABASE = "database"
    CLOUD_RESOURCE = "cloud_resource"
    ENVIRONMENT = "environment"
    PRODUCTION_BOUNDARY = "production_boundary"


class RIMEdgeType(str, Enum):
    CONTAINS = "contains"
    IMPORTS = "imports"
    CALLS = "calls"
    REFERENCES = "references"
    DEFINES = "defines"
    ANNOTATES = "annotates"
    BELONGS_TO_ENVIRONMENT = "belongs_to_environment"
    CROSSES_BOUNDARY = "crosses_boundary"


class RepositoryNode(BaseModel):
    id: str
    label: str
    kind: RIMNodeKind
    source_id: str | None = None
    source_file: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FileNode(RepositoryNode):
    kind: Literal[RIMNodeKind.FILE] = RIMNodeKind.FILE


class FunctionNode(RepositoryNode):
    kind: Literal[RIMNodeKind.FUNCTION] = RIMNodeKind.FUNCTION


class ClassNode(RepositoryNode):
    kind: Literal[RIMNodeKind.CLASS] = RIMNodeKind.CLASS


class SecretNode(RepositoryNode):
    kind: Literal[RIMNodeKind.SECRET] = RIMNodeKind.SECRET


class URLNode(RepositoryNode):
    kind: Literal[RIMNodeKind.URL] = RIMNodeKind.URL


class DatabaseNode(RepositoryNode):
    kind: Literal[RIMNodeKind.DATABASE] = RIMNodeKind.DATABASE


class CloudResourceNode(RepositoryNode):
    kind: Literal[RIMNodeKind.CLOUD_RESOURCE] = RIMNodeKind.CLOUD_RESOURCE


class EnvironmentNode(RepositoryNode):
    kind: Literal[RIMNodeKind.ENVIRONMENT] = RIMNodeKind.ENVIRONMENT


class ProductionBoundaryNode(RepositoryNode):
    kind: Literal[RIMNodeKind.PRODUCTION_BOUNDARY] = RIMNodeKind.PRODUCTION_BOUNDARY


class RIMEdge(BaseModel):
    source: str
    target: str
    type: RIMEdgeType | str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepositoryIntelligenceModel(BaseModel):
    schema_version: str = "0.1"
    nodes: list[RepositoryNode] = Field(default_factory=list)
    edges: list[RIMEdge] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
