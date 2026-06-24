"""Variable tracker - resolves name/value semantics for every assignment.

Interface:
    resolve(parse_result: ParseResult) -> SymbolTable
"""

from __future__ import annotations

import ast
from typing import Optional

from semantic_trace.core.constants import (
    classify_name_semantics,
    classify_value_semantics,
)
from semantic_trace.core.models import (
    AliasFact,
    AliasUseFact,
    ParseResult,
    ReferenceFact,
    SymbolTable,
    ValueFact,
)
from semantic_trace.core.policy_config import DEFAULT_POLICY_CONFIG, PolicyConfig
from semantic_trace.tools.import_graph import resolve_module_to_file


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve(
    parse_result: ParseResult,
    config: PolicyConfig | None = None,
) -> SymbolTable:
    """Build a :class:`SymbolTable` from parsed assignments.

    For each assignment it:
      1. Classifies the target *name* semantics (prod / non_prod / infra).
      2. Extracts the string value (if the RHS is a simple constant) OR
         resolves a dynamically constructed string (``a + b``, f-strings,
         local names, and simple ``from x import NAME`` references).
      3. Classifies the *value* semantics (prod / non_prod / url).
    """
    config = config or DEFAULT_POLICY_CONFIG
    values: list[ValueFact] = []
    references: list[ReferenceFact] = []
    aliases: list[AliasFact] = []
    alias_uses = _extract_alias_uses(parse_result)

    # Per-file map of symbol -> latest RHS AST node, used to resolve local names
    # and simple imported symbols referenced inside constructed strings.
    sym_nodes: dict[str, dict[str, object]] = {}
    for assign in parse_result.assignments:
        if isinstance(assign.value_node, ast.AST):
            sym_nodes.setdefault(assign.file, {})[assign.target] = assign.value_node

    import_symbols = _build_import_symbol_map(parse_result, sym_nodes)

    for assign in parse_result.assignments:
        name_sem = classify_name_semantics(assign.target, config)
        val_str = _extract_string_value(assign.value_node)

        is_constructed = isinstance(assign.value_node, (ast.BinOp, ast.JoinedStr))
        resolved_value: Optional[str] = None
        construction_literals: list[str] = []

        if val_str is not None:
            # Simple string literal - the existing fast path.
            val_sem = classify_value_semantics(val_str, config)
            resolved_value = val_str
        else:
            # Try to resolve a constructed string or a simple imported/local name.
            resolved_value, construction_literals = _resolve_value(
                assign.value_node,
                assign.file,
                sym_nodes,
                import_symbols,
                seen=set(),
                allow_imports=is_constructed,
            )
            if resolved_value is not None:
                val_sem = classify_value_semantics(resolved_value, config)
            else:
                val_sem = set()

        vf = ValueFact(
            symbol=assign.target,
            file=assign.file,
            lineno=assign.lineno,
            value_repr=assign.value_repr,
            value_semantics=val_sem,
            name_semantics=name_sem,
            confidence=1.0,
            resolved_value=resolved_value,
            is_constructed=is_constructed,
            construction_literals=construction_literals,
        )
        values.append(vf)

        # Track references to other names on the RHS.
        rhs_names = _extract_rhs_names(assign.value_node)
        for rname in rhs_names:
            references.append(ReferenceFact(
                source_symbol=assign.target,
                target_symbol=rname,
                file=assign.file,
                lineno=assign.lineno,
            ))

        # Track dict-literal aliases. Values may be direct strings or simple
        # local/imported references that resolve to strings.
        if isinstance(assign.value_node, ast.Dict):
            for key_node, val_node in zip(
                assign.value_node.keys,
                assign.value_node.values,
            ):
                key_str = _const_str(key_node)
                val_str_inner, _lits = _resolve_value(
                    val_node,
                    assign.file,
                    sym_nodes,
                    import_symbols,
                    seen=set(),
                    allow_imports=True,
                )
                if key_str and val_str_inner:
                    alias_sem = classify_value_semantics(val_str_inner, config)
                    if "prod" in alias_sem:
                        aliases.append(AliasFact(
                            alias_name=key_str,
                            original_symbol=val_str_inner,
                            file=assign.file,
                            lineno=assign.lineno,
                            container=assign.target,
                        ))

    return SymbolTable(
        values=values,
        references=references,
        aliases=aliases,
        alias_uses=alias_uses,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_string_value(node: object) -> Optional[str]:
    """Return the string value if *node* is a simple ``ast.Constant(str)``."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _resolve_value(
    node: object,
    current_file: str,
    all_syms: dict[str, dict[str, object]],
    import_symbols: dict[str, dict[str, tuple[str, str]]],
    seen: set[tuple[str, str]],
    allow_imports: bool,
) -> tuple[Optional[str], list[str]]:
    """Resolve *node* to a concrete string via lightweight taint.

    Propagates through:
      - ``ast.Constant(str)``        -> the literal itself
      - ``ast.Name``                 -> local assignment, then simple
                                        imported ``from x import NAME``
      - ``ast.BinOp(Add)``           -> string concatenation
      - ``ast.JoinedStr`` f-string   -> concatenation of parts

    Returns ``(resolved_string | None, leaf_literals)`` where *leaf_literals*
    are the original string literals that fed the result. ``None`` means the
    value could not be statically resolved. The *seen* set guards assignment
    and import cycles.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value, [node.value]

    if isinstance(node, ast.Name):
        local_key = (current_file, node.id)
        if local_key in seen:
            return None, []

        target = all_syms.get(current_file, {}).get(node.id)
        if target is not None:
            return _resolve_value(
                target,
                current_file,
                all_syms,
                import_symbols,
                seen | {local_key},
                allow_imports=allow_imports,
            )

        if not allow_imports:
            return None, []

        imported = import_symbols.get(current_file, {}).get(node.id)
        if imported is None:
            return None, []

        target_file, target_symbol = imported
        imported_key = (target_file, target_symbol)
        if imported_key in seen:
            return None, []

        target = all_syms.get(target_file, {}).get(target_symbol)
        if target is None:
            return None, []

        return _resolve_value(
            target,
            target_file,
            all_syms,
            import_symbols,
            seen | {local_key, imported_key},
            allow_imports=allow_imports,
        )

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, left_lits = _resolve_value(
            node.left,
            current_file,
            all_syms,
            import_symbols,
            seen,
            allow_imports=allow_imports,
        )
        right, right_lits = _resolve_value(
            node.right,
            current_file,
            all_syms,
            import_symbols,
            seen,
            allow_imports=allow_imports,
        )
        if left is None or right is None:
            return None, []
        return left + right, left_lits + right_lits

    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        lits: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
                lits.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                sub, sub_lits = _resolve_value(
                    value.value,
                    current_file,
                    all_syms,
                    import_symbols,
                    seen,
                    allow_imports=allow_imports,
                )
                if sub is None:
                    return None, []
                parts.append(sub)
                lits.extend(sub_lits)
            else:
                return None, []
        return "".join(parts), lits

    return None, []


def _build_import_symbol_map(
    parse_result: ParseResult,
    sym_nodes: dict[str, dict[str, object]],
) -> dict[str, dict[str, tuple[str, str]]]:
    """Return file -> local symbol -> (target file, target symbol).

    This intentionally supports only simple ``from module import NAME`` cases,
    matching the architecture's cross-file taint stretch goal.
    """
    known_files = set(parse_result.files.keys())
    imported: dict[str, dict[str, tuple[str, str]]] = {}

    for imp in parse_result.imports:
        target_file = resolve_module_to_file(imp.module, known_files)
        if target_file is None:
            continue
        target_symbols = sym_nodes.get(target_file, {})
        for name in imp.names:
            if name == "*" or name not in target_symbols:
                continue
            local_name = imp.alias if imp.alias and len(imp.names) == 1 else name
            imported.setdefault(imp.source_file, {})[local_name] = (
                target_file,
                name,
            )

    return imported


def _extract_alias_uses(parse_result: ParseResult) -> list[AliasUseFact]:
    """Find literal dict alias lookups like MAP["x"] and MAP.get("x")."""
    uses: list[AliasUseFact] = []
    seen: set[tuple[str, int, str, str]] = set()

    for file, tree in parse_result.files.items():
        if not isinstance(tree, ast.AST):
            continue
        for node in ast.walk(tree):
            found = _alias_use_from_node(node)
            if found is None:
                continue
            container, qualified, alias_name, access_expr, lineno = found
            key = (file, lineno, qualified, alias_name)
            if key in seen:
                continue
            seen.add(key)
            uses.append(AliasUseFact(
                alias_name=alias_name,
                container=container,
                qualified_container=qualified,
                file=file,
                lineno=lineno,
                access_expr=access_expr,
            ))

    return uses


def _alias_use_from_node(
    node: ast.AST,
) -> tuple[str, str, str, str, int] | None:
    """Extract one literal alias lookup from an AST node, if present."""
    if isinstance(node, ast.Subscript):
        alias_name = _const_str(_subscript_slice(node))
        qualified = _expr_name(node.value)
        if alias_name and qualified:
            return (
                qualified.split(".")[-1],
                qualified,
                alias_name,
                _safe_unparse(node),
                node.lineno,
            )

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
    ):
        alias_name = _const_str(node.args[0])
        qualified = _expr_name(node.func.value)
        if alias_name and qualified:
            return (
                qualified.split(".")[-1],
                qualified,
                alias_name,
                _safe_unparse(node),
                node.lineno,
            )

    return None


def _subscript_slice(node: ast.Subscript) -> object:
    """Return the slice expression, handling older AST wrappers defensively."""
    slice_node = node.slice
    if isinstance(slice_node, ast.Index):  # pragma: no cover on py3.10+
        return slice_node.value
    return slice_node


def _expr_name(node: ast.AST) -> Optional[str]:
    """Return dotted expression names for Name/Attribute chains."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _expr_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def _const_str(node: object) -> Optional[str]:
    """Unwrap a Constant string node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _safe_unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<expression>"


def _extract_rhs_names(node: object) -> list[str]:
    """Return all ``ast.Name.id`` references inside an AST value node."""
    names: list[str] = []
    if not isinstance(node, ast.AST):
        return names
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.append(child.id)
    return names
