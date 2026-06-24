"""Orchestrator — the scripted SemanticTraceAgent.

A deliberately small, deterministic agent loop. It sets a goal, selects the
relevant skills, calls each tool in sequence, records an observation after
every tool, and finally decides which findings to emit — logging the whole
Goal/Thought/Tool/Observation/Decision trace so the reasoning is visible.

Autonomy is intentionally not required (see history.md): the value is in
*showing* the agentic structure over deterministic detection, not in letting a
model improvise the pipeline.

Interface:
    run(goal, root) -> AgentRunResult
    format_trace(result) -> str
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Union

from semantic_trace.brain import explainer, skills
from semantic_trace.core.models import AgentRunResult, TraceStep
from semantic_trace.core.policy_config import PolicyConfig
from semantic_trace.tools import (
    ast_parser,
    import_graph,
    path_finder,
    policy_evaluator,
    variable_tracker,
)

DEFAULT_GOAL = (
    "Detect whether the target project contains non-production code, "
    "variables, configs, or execution paths that can reach production resources."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run(
    goal: str,
    root: Union[str, Path],
    policy_config: PolicyConfig | None = None,
    use_llm: bool = False,
) -> AgentRunResult:
    """Execute the scripted agent loop against *root* and return the result."""
    goal = goal or DEFAULT_GOAL
    root_path = Path(root).resolve()
    result = AgentRunResult(goal=goal, root=str(root_path))
    trace = result.trace

    # --- Goal -------------------------------------------------------------
    trace.append(TraceStep("Goal", goal))

    selected = skills.policies_for_goal(goal)
    trace.append(TraceStep(
        "Thought",
        "To answer this I need semantic facts, import reachability, taint "
        "propagation, and alias resolution. Selecting policies: "
        + ", ".join(selected) + ".",
        data={"policies": selected},
    ))

    # --- Tool 1: AST parser ----------------------------------------------
    trace.append(TraceStep("Tool", "ast_parser.scan_project", data={"root": str(root_path)}))
    pr = ast_parser.scan_project(root_path)
    trace.append(TraceStep(
        "Observation",
        f"Parsed {len(pr.files)} file(s): {len(pr.imports)} imports, "
        f"{len(pr.assignments)} assignments, {len(pr.functions)} functions.",
        data={
            "files": len(pr.files),
            "imports": len(pr.imports),
            "assignments": len(pr.assignments),
            "functions": len(pr.functions),
        },
    ))

    # --- Tool 2: Variable tracker ----------------------------------------
    trace.append(TraceStep("Thought",
                           "I need to know which values/aliases are production-tainted, "
                           "including dynamically constructed strings."))
    trace.append(TraceStep("Tool", "variable_tracker.resolve"))
    st = variable_tracker.resolve(pr, config=policy_config)
    prod_syms = [v.symbol for v in st.values if "prod" in v.value_semantics]
    constructed = [v.symbol for v in st.values if v.is_constructed and v.resolved_value]
    trace.append(TraceStep(
        "Observation",
        f"Production-tainted symbols: {', '.join(prod_syms) or 'none'}. "
        f"Constructed strings: {', '.join(constructed) or 'none'}. "
        f"Dict aliases: {len(st.aliases)}. Alias consumers: {len(st.alias_uses)}.",
        data={
            "prod_symbols": prod_syms,
            "constructed": constructed,
            "aliases": [a.alias_name for a in st.aliases],
            "alias_uses": [a.access_expr for a in st.alias_uses],
        },
    ))

    # --- Tool 3: Import graph + path finder ------------------------------
    trace.append(TraceStep("Thought",
                           "I need to prove reachability from non-production code to "
                           "production sinks."))
    trace.append(TraceStep("Tool", "import_graph.build + path_finder"))
    graph = import_graph.build(pr)
    sink_files = sorted({v.file for v in st.values if "prod" in v.value_semantics})
    reachable = {}
    for sink in sink_files:
        # who can reach this sink (for the trace narrative)
        sources = [n for n in graph.nodes
                   if n not in sink_files and path_finder.find_reachable_sinks(graph, n, [sink])]
        if sources:
            reachable[sink] = sources
    trace.append(TraceStep(
        "Observation",
        f"Import graph: {graph.number_of_nodes()} nodes, "
        f"{graph.number_of_edges()} edges. Production sink files: "
        f"{', '.join(sink_files) or 'none'}.",
        data={"sinks": sink_files, "reachable_from": reachable},
    ))

    # --- Tool 4: Policy evaluator ----------------------------------------
    trace.append(TraceStep("Thought",
                           "Now I can evaluate every selected policy against the facts."))
    trace.append(TraceStep("Tool", "policy_evaluator.evaluate"))
    findings = policy_evaluator.evaluate(pr, st, graph, config=policy_config)
    findings = [f for f in findings if f.policy_id in selected]
    findings = policy_evaluator.rank_findings(findings)

    # Enrich each finding with a concise explanation from the explainer skill.
    for f in findings:
        f.explanation = explainer.explain(f, graph, st, use_llm=use_llm)

    by_policy = Counter(f.policy_id for f in findings)
    trace.append(TraceStep(
        "Observation",
        f"Evaluated policies. Findings: "
        + (", ".join(f"{p}:{by_policy[p]}" for p in selected if by_policy[p]) or "none"),
        data={"by_policy": dict(by_policy)},
    ))

    # --- Decision ---------------------------------------------------------
    result.findings = findings
    if findings:
        decision = (
            f"Emit {len(findings)} finding(s) across "
            f"{len(by_policy)} policy type(s). The target is NOT clean: "
            f"non-production code can reach production resources."
        )
    else:
        decision = (
            "Emit no findings. The target appears clean: no non-production "
            "path reaches a production resource."
        )
    trace.append(TraceStep("Decision", decision, data={"by_policy": dict(by_policy)}))
    result.summary = decision

    return result


# ---------------------------------------------------------------------------
# Trace rendering
# ---------------------------------------------------------------------------

def format_trace(result: AgentRunResult) -> str:
    """Render the agent trace as readable plain text."""
    lines: list[str] = []
    lines.append(f"Goal root: {result.root}")
    lines.append("")
    for step in result.trace:
        lines.append(f"{step.phase}:")
        for sub in step.text.splitlines() or [""]:
            lines.append(f"    {sub}")
    return "\n".join(lines)
