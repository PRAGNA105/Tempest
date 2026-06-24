"""Policy evaluator - deterministic P10-P14 rule evaluation.

Interface:
    evaluate(parse_result, symbol_table, graph) -> list[Finding]

Implements all five demo policies:
    P10  prod-named variable masking a local/placeholder value
    P11  production value inside a non-production file
    P12  multi-hop import chain from non-prod code to a production sink
    P13  dynamically constructed production endpoint
    P14  aliased production identifier hidden behind a dict key
"""

from __future__ import annotations

from collections import defaultdict

import networkx as nx

from semantic_trace.core.constants import (
    POLICY_P10,
    POLICY_P11,
    POLICY_P12,
    POLICY_P13,
    POLICY_P14,
    classify_value_semantics,
    is_non_prod_path,
)
from semantic_trace.core.models import (
    AliasUseFact,
    Finding,
    ParseResult,
    SymbolTable,
    ValueFact,
)
from semantic_trace.core.policy_config import DEFAULT_POLICY_CONFIG, PolicyConfig
from semantic_trace.tools import path_finder


SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate(
    parse_result: ParseResult,
    symbol_table: SymbolTable,
    graph: nx.DiGraph,
    config: PolicyConfig | None = None,
) -> list[Finding]:
    """Run all enabled policy rules and return ranked findings (P10-P14)."""
    config = config or DEFAULT_POLICY_CONFIG
    findings: list[Finding] = []
    findings.extend(_eval_p10(symbol_table))
    findings.extend(_eval_p11(symbol_table, config))
    findings.extend(_eval_p12(parse_result, symbol_table, graph))
    findings.extend(_eval_p13(symbol_table, config))
    findings.extend(_eval_p14(symbol_table, config))
    return rank_findings(findings)


def rank_findings(findings: list[Finding]) -> list[Finding]:
    """Return findings ordered for the final report.

    High severity appears first, then policy id. P12 chains are grouped by
    shared sink and ordered longest-first inside each sink group.
    """
    return sorted(findings, key=_finding_rank_key)


# ---------------------------------------------------------------------------
# P10 - Prod-named variable masking a local / placeholder value
# ---------------------------------------------------------------------------

def _eval_p10(symbol_table: SymbolTable) -> list[Finding]:
    """Detect variables whose name claims production but value is local/dev."""
    findings: list[Finding] = []

    for vf in symbol_table.values:
        if "prod" not in vf.name_semantics:
            continue
        if "non_prod" not in vf.value_semantics:
            continue
        if "prod" in vf.value_semantics:
            continue

        findings.append(Finding(
            policy_id=POLICY_P10,
            severity="medium",
            title=(
                f"Production-named variable masks a non-production value: "
                f"{vf.symbol} in {vf.file}"
            ),
            file=vf.file,
            lineno=vf.lineno,
            source_node=vf.symbol,
            sink_node=vf.symbol,
            evidence=[
                f"Variable: {vf.symbol}",
                f"Value: {vf.value_repr}",
                f"Name semantics: {sorted(vf.name_semantics)} (claims production)",
                f"Value semantics: {sorted(vf.value_semantics)} (resolves non-production)",
            ],
            explanation=(
                f"The variable '{vf.symbol}' is named like a production "
                f"resource, but its value {vf.value_repr} resolves to a "
                f"local/staging/placeholder endpoint. Code that trusts the "
                f"name would believe it is talking to production while it is "
                f"actually pointing somewhere non-production."
            ),
            confidence=0.9,
        ))

    return findings


# ---------------------------------------------------------------------------
# P11 - Production URLs inside non-production configuration
# ---------------------------------------------------------------------------

def _eval_p11(
    symbol_table: SymbolTable,
    config: PolicyConfig,
) -> list[Finding]:
    """Detect production-valued assignments living in non-prod files."""
    findings: list[Finding] = []

    for vf in symbol_table.values:
        if not is_non_prod_path(vf.file, config):
            continue
        if "prod" not in vf.value_semantics:
            continue

        findings.append(Finding(
            policy_id=POLICY_P11,
            severity="high",
            title=(
                f"Production value in non-production file: "
                f"{vf.symbol} in {vf.file}"
            ),
            file=vf.file,
            lineno=vf.lineno,
            source_node=vf.file,
            sink_node=vf.symbol,
            evidence=[
                f"Variable: {vf.symbol}",
                f"Value: {vf.value_repr}",
                f"File classified as non-production: {vf.file}",
                f"Value semantics: {sorted(vf.value_semantics)}",
            ],
            explanation=(
                f"The file '{vf.file}' is in a non-production context "
                f"(path contains staging/dev/test/demo), but the variable "
                f"'{vf.symbol}' holds a production value: {vf.value_repr}. "
                f"This means non-production code has a direct handle to a "
                f"production resource."
            ),
            confidence=1.0,
        ))

    return findings


# ---------------------------------------------------------------------------
# P12 - Multi-hop import chain from non-prod code to production sinks
# ---------------------------------------------------------------------------

def _eval_p12(
    parse_result: ParseResult,
    symbol_table: SymbolTable,
    graph: nx.DiGraph,
) -> list[Finding]:
    """Detect import chains from non-prod entry files to prod-valued files."""
    sink_files: set[str] = set()
    prod_symbols_by_file: dict[str, list[ValueFact]] = {}
    for vf in symbol_table.values:
        if "prod" in vf.value_semantics:
            sink_files.add(vf.file)
            prod_symbols_by_file.setdefault(vf.file, []).append(vf)

    if not sink_files:
        return []

    start_files = set(graph.nodes) - sink_files
    paths = path_finder.find_paths(graph, start_files, sink_files)

    longest_by_pair: dict[tuple[str, str], list[str]] = {}
    for path in paths:
        if len(path) < 2:
            continue
        pair = (path[0], path[-1])
        existing = longest_by_pair.get(pair)
        if existing is None or len(path) > len(existing):
            longest_by_pair[pair] = list(path)

    ranked = sorted(
        longest_by_pair.values(),
        key=lambda p: (-len(p), p[-1], p[0]),
    )

    findings: list[Finding] = []

    for path in ranked:
        start = path[0]
        end = path[-1]
        prod_vars = prod_symbols_by_file.get(end, [])
        prod_var_names = ", ".join(v.symbol for v in prod_vars)
        chain_str = " -> ".join(path)

        findings.append(Finding(
            policy_id=POLICY_P12,
            severity="high",
            title=(
                f"Multi-hop import chain to production sink: "
                f"{start} -> ... -> {end}"
            ),
            file=start,
            lineno=None,
            source_node=start,
            sink_node=end,
            path=list(path),
            evidence=[
                f"Chain: {chain_str}",
                f"Production symbols at sink: {prod_var_names}",
                f"Chain length: {len(path)} files ({len(path)-1} hops)",
            ],
            explanation=(
                f"The file '{start}' can reach production resources through "
                f"a {len(path)-1}-hop import chain: {chain_str}. "
                f"The sink file '{end}' contains production-tainted symbols: "
                f"{prod_var_names}. This means non-production code has a "
                f"transitive dependency on production configuration."
            ),
            confidence=1.0,
        ))

    return findings


# ---------------------------------------------------------------------------
# P13 - Dynamically constructed production endpoint
# ---------------------------------------------------------------------------

def _eval_p13(
    symbol_table: SymbolTable,
    config: PolicyConfig,
) -> list[Finding]:
    """Detect production endpoints assembled from fragments."""
    findings: list[Finding] = []

    for vf in symbol_table.values:
        if not vf.is_constructed or vf.resolved_value is None:
            continue
        resolved_sem = classify_value_semantics(vf.resolved_value, config)
        if not {"prod", "url"} <= resolved_sem:
            continue
        if any(
            {"prod", "url"} <= classify_value_semantics(lit, config)
            for lit in vf.construction_literals
        ):
            continue

        literal_list = ", ".join(repr(lit) for lit in vf.construction_literals)
        findings.append(Finding(
            policy_id=POLICY_P13,
            severity="high",
            title=(
                f"Dynamically constructed production endpoint: "
                f"{vf.symbol} in {vf.file}"
            ),
            file=vf.file,
            lineno=vf.lineno,
            source_node=vf.symbol,
            sink_node=vf.symbol,
            evidence=[
                f"Variable: {vf.symbol}",
                f"Construction: {vf.value_repr}",
                f"Resolved value: {vf.resolved_value}",
                f"Contributing literals: {literal_list}",
                f"Resolved semantics: {sorted(resolved_sem)}",
            ],
            explanation=(
                f"The variable '{vf.symbol}' is assembled from fragments "
                f"({vf.value_repr}) that individually look harmless, but the "
                f"resolved string '{vf.resolved_value}' is a production "
                f"endpoint. No single literal contains the full URL, so a "
                f"naive scanner matching complete connection strings would "
                f"miss it."
            ),
            confidence=0.95,
        ))

    return findings


# ---------------------------------------------------------------------------
# P14 - Aliased production identifier hidden behind a dict key
# ---------------------------------------------------------------------------

def _eval_p14(
    symbol_table: SymbolTable,
    config: PolicyConfig,
) -> list[Finding]:
    """Detect production URLs hidden behind innocent dict keys."""
    findings: list[Finding] = []
    uses_by_alias = _alias_uses_by_container_and_key(symbol_table.alias_uses)

    for alias in symbol_table.aliases:
        container = alias.container or "<dict>"
        consumers = uses_by_alias.get((container, alias.alias_name), [])
        evidence = [
            f"Dictionary: {container}",
            f"Alias key: {alias.alias_name!r}",
            f"Resolves to: {alias.original_symbol}",
            f"Value semantics: {sorted(classify_value_semantics(alias.original_symbol, config))}",
        ]
        if consumers:
            evidence.extend(
                f"Consumer: {use.file}:{use.lineno} uses {use.access_expr}"
                for use in consumers
            )

        findings.append(Finding(
            policy_id=POLICY_P14,
            severity="high",
            title=(
                f"Aliased production identifier: "
                f"{container}[{alias.alias_name!r}] in {alias.file}"
            ),
            file=alias.file,
            lineno=alias.lineno,
            source_node=alias.alias_name,
            sink_node=alias.original_symbol,
            evidence=evidence,
            explanation=(
                f"The dictionary '{container}' in '{alias.file}' maps the "
                f"innocent key {alias.alias_name!r} to the production endpoint "
                f"'{alias.original_symbol}'. Any code that looks up "
                f"{container}[{alias.alias_name!r}] reaches a production "
                f"resource without ever referencing it by a production-looking "
                f"name."
            ),
            confidence=0.95,
        ))

    return findings


def _alias_uses_by_container_and_key(
    uses: list[AliasUseFact],
) -> dict[tuple[str, str], list[AliasUseFact]]:
    grouped: dict[tuple[str, str], list[AliasUseFact]] = defaultdict(list)
    for use in uses:
        grouped[(use.container, use.alias_name)].append(use)
    for entries in grouped.values():
        entries.sort(key=lambda use: (use.file, use.lineno, use.access_expr))
    return dict(grouped)


def _finding_rank_key(finding: Finding) -> tuple:
    return (
        SEVERITY_ORDER.get(finding.severity, 99),
        finding.policy_id,
        finding.sink_node if finding.policy_id == POLICY_P12 else "",
        -len(finding.path),
        finding.file,
        finding.lineno or 0,
        finding.title,
    )
