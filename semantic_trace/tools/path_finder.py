"""Path finder — BFS/DFS reachability over the import graph.

Interface:
    find_paths(graph, start_files, sink_files) -> list[list[str]]
"""

from __future__ import annotations

from collections import deque
from typing import Iterable

import networkx as nx


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_paths(
    graph: nx.DiGraph,
    start_files: Iterable[str],
    sink_files: Iterable[str],
) -> list[list[str]]:
    """Return all simple paths from any *start_file* to any *sink_file*.

    Uses ``nx.all_simple_paths`` for correctness (the graph is small).
    Each path is a list of file nodes, e.g.
    ``["services/payment.py", "data/db_client.py", "config/aliases.py", "config/staging.py"]``.
    """
    sink_set = set(sink_files)
    paths: list[list[str]] = []

    for src in start_files:
        if src not in graph:
            continue
        for sink in sink_set:
            if sink not in graph:
                continue
            for path in nx.all_simple_paths(graph, src, sink):
                paths.append(list(path))

    return paths


def find_reachable_sinks(
    graph: nx.DiGraph,
    start_file: str,
    sink_files: Iterable[str],
) -> list[str]:
    """Return the subset of *sink_files* reachable from *start_file*."""
    if start_file not in graph:
        return []
    reachable = nx.descendants(graph, start_file) | {start_file}
    return [s for s in sink_files if s in reachable]
