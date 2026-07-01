from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from graph import RepositoryGraph


class GraphifyAdapter(ABC):
    """Boundary between Graphify and RILDE contracts."""

    @abstractmethod
    def build_graph(self, repository_path: Path) -> RepositoryGraph:
        """Build a repository graph from a repository path."""

