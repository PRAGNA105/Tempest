from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from graph import Edge, Node, RepositoryGraph
from graphify_adapter.base import GraphifyAdapter


DEFAULT_GRAPHIFY_OUTPUT = Path("graphify-out") / "graph.json"

CONFIDENCE_DEFAULTS = {
    "EXTRACTED": 1.0,
    "INFERRED": 0.75,
    "AMBIGUOUS": 0.5,
}


class GraphifyJsonAdapter(GraphifyAdapter):
    """Loads Graphify's NetworkX node-link JSON into RILDE's graph contract."""

    def __init__(self, graph_json: Path | None = None) -> None:
        self.graph_json = graph_json

    def build_graph(self, repository_path: Path) -> RepositoryGraph:
        graph_path = self.graph_json or repository_path / DEFAULT_GRAPHIFY_OUTPUT
        return self.load_graph_json(graph_path)

    def load_graph_json(self, graph_path: Path) -> RepositoryGraph:
        if not graph_path.exists():
            raise FileNotFoundError(f"Graphify graph JSON not found: {graph_path}")

        data = json.loads(graph_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Graphify graph JSON must be an object")

        nodes = [_to_node(raw_node) for raw_node in _items(data, "nodes")]
        edges = [_to_edge(raw_edge) for raw_edge in _edge_items(data)]

        return RepositoryGraph(
            nodes=nodes,
            edges=[edge for edge in edges if edge is not None],
            metadata={
                "adapter": "graphify_json",
                "graph_path": str(graph_path),
                "graphify_format": "networkx_node_link",
                "directed": data.get("directed"),
                "multigraph": data.get("multigraph"),
                "graph": data.get("graph", {}),
            },
        )


def _items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    values = data.get(key, [])
    if not isinstance(values, list):
        raise ValueError(f"Graphify graph JSON field '{key}' must be a list")
    return [value for value in values if isinstance(value, dict)]


def _edge_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    key = "links" if "links" in data else "edges"
    return _items(data, key)


def _to_node(raw: dict[str, Any]) -> Node:
    node_id = str(raw["id"])
    source_file = raw.get("source_file") or raw.get("source")
    node_type = (
        raw.get("type")
        or raw.get("kind")
        or raw.get("node_type")
        or raw.get("entity_type")
        or raw.get("file_type")
        or "unknown"
    )

    metadata = {
        key: value
        for key, value in raw.items()
        if key not in {"id", "label", "source_file", "source"}
    }

    return Node(
        id=node_id,
        label=str(raw.get("label") or node_id),
        type=str(node_type),
        source_file=str(source_file) if source_file else None,
        metadata=metadata,
    )


def _to_edge(raw: dict[str, Any]) -> Edge | None:
    source = raw.get("source")
    target = raw.get("target")
    if source is None or target is None:
        return None

    graphify_confidence = raw.get("confidence")
    confidence = _numeric_confidence(graphify_confidence, raw.get("confidence_score"))
    metadata = {
        key: value
        for key, value in raw.items()
        if key not in {"source", "target", "relation", "confidence", "source_file"}
    }
    metadata["graphify_confidence"] = graphify_confidence

    return Edge(
        source=str(source),
        target=str(target),
        relation=str(raw.get("relation") or "related_to"),
        confidence=confidence,
        source_file=str(raw["source_file"]) if raw.get("source_file") else None,
        metadata=metadata,
    )


def _numeric_confidence(raw_confidence: Any, raw_score: Any) -> float:
    if isinstance(raw_confidence, int | float):
        return _clamp(float(raw_confidence))

    if isinstance(raw_confidence, str):
        tag = raw_confidence.upper()
        if tag == "INFERRED" and isinstance(raw_score, int | float):
            return _clamp(float(raw_score))
        return CONFIDENCE_DEFAULTS.get(tag, 1.0)

    if isinstance(raw_score, int | float):
        return _clamp(float(raw_score))

    return 1.0


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))

