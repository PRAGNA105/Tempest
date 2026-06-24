"""Import graph builder — turns ImportFacts into a NetworkX DiGraph.

Interface:
    build(parse_result: ParseResult) -> networkx.DiGraph
"""

from __future__ import annotations

import networkx as nx

from semantic_trace.core.models import ParseResult


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build(parse_result: ParseResult) -> nx.DiGraph:
    """Build a file-level import graph from *parse_result*.

    Nodes are relative POSIX file paths (e.g. ``config/staging.py``).
    Edges carry ``type="IMPORTS"`` plus the originating ``lineno``.
    """
    graph = nx.DiGraph()

    known_files = set(parse_result.files.keys())

    # Add every parsed file as a node
    for fpath in known_files:
        graph.add_node(fpath, type="File", name=fpath)

    # Add IMPORTS edges
    for imp in parse_result.imports:
        target_path = resolve_module_to_file(imp.module, known_files)
        if target_path is not None:
            graph.add_edge(
                imp.source_file,
                target_path,
                type="IMPORTS",
                lineno=imp.lineno,
                module=imp.module,
                names=imp.names,
            )

        # Also resolve imported names as potential sub-modules.
        # E.g. ``from demo_app.data import db_client`` has module="demo_app.data"
        # and names=["db_client"]. The name "db_client" might be a submodule
        # (data/db_client.py) rather than a symbol in data/__init__.py.
        for name in imp.names:
            sub_module = f"{imp.module}.{name}"
            sub_path = resolve_module_to_file(sub_module, known_files)
            if sub_path is not None and sub_path != target_path:
                graph.add_edge(
                    imp.source_file,
                    sub_path,
                    type="IMPORTS",
                    lineno=imp.lineno,
                    module=sub_module,
                    names=[name],
                )

    return graph


# ---------------------------------------------------------------------------
# Module resolution
# ---------------------------------------------------------------------------

def resolve_module_to_file(
    module: str,
    known_files: set[str],
) -> str | None:
    """Convert a dotted module path to the best-matching known file.

    Strategy (in order):
      1. ``a.b.c`` → ``a/b/c.py``
      2. ``a.b.c`` → ``a/b/c/__init__.py``
      3. Strip the leftmost component and retry (handles package-prefixed
         imports like ``demo_app.config.staging``).

    Returns ``None`` if no known file matches.
    """
    parts = module.split(".")

    # Try with all parts, then progressively strip the leading component
    for start in range(len(parts)):
        sub = parts[start:]
        if not sub:
            break
        candidate = "/".join(sub) + ".py"
        if candidate in known_files:
            return candidate
        candidate_pkg = "/".join(sub) + "/__init__.py"
        if candidate_pkg in known_files:
            return candidate_pkg

    return None


_resolve_module_to_file = resolve_module_to_file
