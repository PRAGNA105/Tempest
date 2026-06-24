"""AST parser — walks a project tree and extracts structural facts.

Interface:
    scan_project(root: str | Path) -> ParseResult
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Union

from semantic_trace.core.models import (
    AssignmentFact,
    FunctionFact,
    ImportFact,
    ParseResult,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_project(root: Union[str, Path]) -> ParseResult:
    """Recursively parse all ``.py`` files under *root*.

    Returns a :class:`ParseResult` containing the parsed AST modules and
    the extracted import, assignment, and function facts.
    """
    root = Path(root).resolve()
    files: dict[str, ast.Module | None] = {}
    imports: list[ImportFact] = []
    assignments: list[AssignmentFact] = []
    functions: list[FunctionFact] = []

    for dirpath, _dirs, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(root).as_posix()
            try:
                source = fpath.read_text(encoding="utf-8")
                tree = ast.parse(source, filename=rel)
            except (SyntaxError, UnicodeDecodeError):
                files[rel] = None
                continue

            files[rel] = tree
            imports.extend(_extract_imports(tree, rel))
            assignments.extend(_extract_assignments(tree, rel, source))
            functions.extend(_extract_functions(tree, rel))

    return ParseResult(
        files=files,
        imports=imports,
        assignments=assignments,
        functions=functions,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_imports(tree: ast.Module, rel_path: str) -> list[ImportFact]:
    """Extract ``import`` and ``from … import`` statements."""
    facts: list[ImportFact] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [alias.name for alias in node.names]
            facts.append(ImportFact(
                source_file=rel_path,
                module=node.module,
                names=names,
                lineno=node.lineno,
                alias=node.names[0].asname if len(node.names) == 1 else None,
            ))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                facts.append(ImportFact(
                    source_file=rel_path,
                    module=alias.name,
                    names=[alias.name.split(".")[-1]],
                    lineno=node.lineno,
                    alias=alias.asname,
                ))
    return facts


def _extract_assignments(
    tree: ast.Module,
    rel_path: str,
    source: str,
) -> list[AssignmentFact]:
    """Extract module-level assignments (``ast.Assign`` / ``ast.AnnAssign``)."""
    facts: list[AssignmentFact] = []
    for node in ast.iter_child_nodes(tree):
        targets: list[str] = []
        value_node = None

        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    targets.append(t.id)
            value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets.append(node.target.id)
            value_node = node.value

        if not targets or value_node is None:
            continue

        value_repr = _safe_unparse(value_node, source, node.lineno)

        for tname in targets:
            facts.append(AssignmentFact(
                file=rel_path,
                target=tname,
                value_repr=value_repr,
                value_node=value_node,
                lineno=node.lineno,
            ))
    return facts


def _extract_functions(tree: ast.Module, rel_path: str) -> list[FunctionFact]:
    """Extract top-level function definitions."""
    facts: list[FunctionFact] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            facts.append(FunctionFact(
                file=rel_path,
                name=node.name,
                lineno=node.lineno,
                args=args,
            ))
    return facts


def _safe_unparse(node: ast.AST, source: str, lineno: int) -> str:
    """Try ``ast.unparse``; fall back to a source-line snippet."""
    try:
        return ast.unparse(node)
    except Exception:
        lines = source.splitlines()
        if 0 < lineno <= len(lines):
            return lines[lineno - 1].strip()
        return "<unknown>"
