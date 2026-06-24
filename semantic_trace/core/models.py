"""Data structures for the semantic trace Graph Engine.

Every structure here is a plain dataclass that can be serialised into
NetworkX node/edge attributes or printed as JSON for the agent trace.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Graph primitives
# ---------------------------------------------------------------------------

@dataclass
class Node:
    """A node in the semantic graph (file, variable, function, or sink)."""

    id: str
    type: str  # "File" | "Variable" | "Function" | "ProductionSink"
    name: str
    file: str
    lineno: Optional[int] = None
    attrs: dict = field(default_factory=dict)


@dataclass
class Edge:
    """A directed edge in the semantic graph."""

    src: str
    dst: str
    type: str  # "IMPORTS" | "ASSIGNS" | "REFERENCES" | "CALLS"
    file: Optional[str] = None
    lineno: Optional[int] = None
    attrs: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# AST-extracted facts
# ---------------------------------------------------------------------------

@dataclass
class ImportFact:
    """One import statement extracted from source."""

    source_file: str
    module: str          # dotted module path, e.g. "demo_app.config.staging"
    names: list[str]     # imported names, e.g. ["PROD_DB_URL"]
    lineno: int
    alias: Optional[str] = None  # if ``import X as alias``


@dataclass
class AssignmentFact:
    """One top-level assignment extracted from source."""

    file: str
    target: str          # variable name
    value_repr: str      # repr of AST value node
    value_node: object = None  # raw ast node, not serialised
    lineno: int = 0


@dataclass
class FunctionFact:
    """A function definition extracted from source."""

    file: str
    name: str
    lineno: int
    args: list[str] = field(default_factory=list)


@dataclass
class ParseResult:
    """Aggregated output from ast_parser.scan_project()."""

    files: dict  # path -> ast.Module (or None on parse failure)
    imports: list[ImportFact] = field(default_factory=list)
    assignments: list[AssignmentFact] = field(default_factory=list)
    functions: list[FunctionFact] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Semantic analysis facts
# ---------------------------------------------------------------------------

@dataclass
class ValueFact:
    """A resolved symbol with name and value semantic tags.

    For dynamically constructed strings (``BASE + HOST + "/maindb"`` or
    f-strings) the lightweight taint resolver populates ``resolved_value``
    with the fully assembled string, marks ``is_constructed`` True, and lists
    the contributing leaf literals in ``construction_literals``. These power
    P13 (dynamic construction) without changing the simple-literal path.
    """

    symbol: str
    file: str
    lineno: int
    value_repr: str
    value_semantics: set[str] = field(default_factory=set)
    name_semantics: set[str] = field(default_factory=set)
    references: list[str] = field(default_factory=list)
    confidence: float = 1.0
    resolved_value: Optional[str] = None
    is_constructed: bool = False
    construction_literals: list[str] = field(default_factory=list)


@dataclass
class ReferenceFact:
    """A reference from one symbol to another."""

    source_symbol: str
    target_symbol: str
    file: str
    lineno: int


@dataclass
class AliasFact:
    """An alias (dict key, re-assignment) that hides a production value."""

    alias_name: str
    original_symbol: str
    file: str
    lineno: int
    container: Optional[str] = None  # e.g. dict name


@dataclass
class AliasUseFact:
    """A literal lookup of a known alias container, e.g. MAP["payments"]."""

    alias_name: str
    container: str
    qualified_container: str
    file: str
    lineno: int
    access_expr: str


@dataclass
class SymbolTable:
    """Aggregated output from variable_tracker.resolve()."""

    values: list[ValueFact] = field(default_factory=list)
    references: list[ReferenceFact] = field(default_factory=list)
    aliases: list[AliasFact] = field(default_factory=list)
    alias_uses: list[AliasUseFact] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single policy violation detected by the Graph Engine."""

    id: str = field(default_factory=lambda: f"F-{uuid.uuid4().hex[:8]}")
    policy_id: str = ""      # "P10" | "P11" | "P12" | "P13" | "P14"
    severity: str = "medium"  # "low" | "medium" | "high"
    title: str = ""
    file: str = ""
    lineno: Optional[int] = None
    source_node: Optional[str] = None
    sink_node: Optional[str] = None
    path: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    explanation: str = ""
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Agent trace
# ---------------------------------------------------------------------------

@dataclass
class TraceStep:
    """One step in the scripted Goal/Thought/Tool/Observation/Decision loop."""

    phase: str          # "Goal" | "Thought" | "Tool" | "Observation" | "Decision"
    text: str
    data: dict = field(default_factory=dict)


@dataclass
class AgentRunResult:
    """Aggregated output from orchestrator.run()."""

    goal: str
    root: str
    trace: list[TraceStep] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    summary: str = ""
