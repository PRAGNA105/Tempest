from __future__ import annotations

from pathlib import Path

from graph import Node, RepositoryGraph
from graphify_adapter.base import GraphifyAdapter


class StubGraphifyAdapter(GraphifyAdapter):
    """Placeholder adapter used until the real Graphify integration is wired in."""

    def build_graph(self, repository_path: Path) -> RepositoryGraph:
        resolved = repository_path.resolve()
        return RepositoryGraph(
            nodes=[
                Node(
                    id="repo:root",
                    label=resolved.name,
                    type="repository",
                    source_file=None,
                    metadata={"path": str(resolved)},
                )
            ],
            edges=[],
            metadata={"adapter": "stub_graphify", "repository_path": str(resolved)},
        )

