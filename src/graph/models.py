from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Node(BaseModel):
    """Language-agnostic repository graph node."""

    id: str
    label: str
    type: str
    source_file: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """Language-agnostic repository graph relationship."""

    source: str
    target: str
    relation: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_file: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RepositoryGraph(BaseModel):
    """Raw graph emitted by Graphify or a compatible adapter."""

    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def node_ids(self) -> set[str]:
        return {node.id for node in self.nodes}

