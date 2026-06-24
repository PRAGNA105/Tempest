"""Explainer — concise, human-readable explanations from finding evidence.

Detection is deterministic; this module turns a :class:`Finding` into a short
narrative a reviewer can read at a glance. It is template-based per policy and
needs no model. An optional local-LLM polish hook (`use_llm=True`) is provided
for completeness but defaults to off so the demo stays offline and repeatable.

Interface:
    explain(finding, graph=None, symbol_table=None, use_llm=False) -> str
"""

from __future__ import annotations

import os
import shlex
import subprocess
from typing import Optional

import networkx as nx

from semantic_trace.core.constants import (
    POLICY_P10,
    POLICY_P11,
    POLICY_P12,
    POLICY_P13,
    POLICY_P14,
)
from semantic_trace.core.models import Finding, SymbolTable


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def explain(
    finding: Finding,
    graph: Optional[nx.DiGraph] = None,
    symbol_table: Optional[SymbolTable] = None,
    use_llm: bool = False,
) -> str:
    """Return a one-paragraph explanation for *finding*.

    The deterministic template uses the finding's own fields plus optional
    graph context (for P12 chains). When *use_llm* is True a local model may
    be used to polish the wording; if no model is wired it silently falls back
    to the deterministic text so behaviour never depends on the LLM.
    """
    builder = _BUILDERS.get(finding.policy_id, _explain_generic)
    text = builder(finding, graph, symbol_table)

    if use_llm:
        text = _maybe_llm_polish(text, finding)

    return text


# ---------------------------------------------------------------------------
# Per-policy templates
# ---------------------------------------------------------------------------

def _explain_p10(finding, graph, st) -> str:
    return (
        f"P10 - Masked production name. '{finding.source_node}' in "
        f"{_loc(finding)} reads like a production handle, but its value "
        f"resolves to a non-production endpoint. The reassuring name hides a "
        f"throwaway target; anyone trusting it would silently miss production."
    )


def _explain_p11(finding, graph, st) -> str:
    return (
        f"P11 - Production value in a non-production file. {_loc(finding)} "
        f"is a non-production location, yet it hardcodes a production "
        f"resource via '{finding.sink_node}'. Non-production code therefore "
        f"holds a direct handle to production."
    )


def _explain_p12(finding, graph, st) -> str:
    chain = " -> ".join(finding.path) if finding.path else f"{finding.source_node} -> {finding.sink_node}"
    hops = max(len(finding.path) - 1, 1)
    return (
        f"P12 - Reachable production sink. '{finding.source_node}' reaches "
        f"production in {hops} hop(s): {chain}. The terminal file holds "
        f"production-tainted symbols, so importing the entry point transitively "
        f"pulls in production configuration."
    )


def _explain_p13(finding, graph, st) -> str:
    resolved = _evidence_value(finding, "Resolved value:")
    return (
        f"P13 - Constructed production endpoint. '{finding.source_node}' in "
        f"{_loc(finding)} is assembled from fragments that look harmless "
        f"individually, but resolve to a production endpoint"
        + (f" ({resolved})" if resolved else "")
        + ". No single literal contains the full URL, so whole-string scanners "
        f"miss it."
    )


def _explain_p14(finding, graph, st) -> str:
    consumer = _evidence_value(finding, "Consumer:")
    text = (
        f"P14 - Aliased production identifier. {_loc(finding)} maps an "
        f"innocent key '{finding.source_node}' to the production endpoint "
        f"'{finding.sink_node}'. Callers reach production through the alias "
        f"without ever naming a production resource."
    )
    if consumer:
        text += f" Observed consumer: {consumer}."
    return text


def _explain_generic(finding, graph, st) -> str:
    return finding.explanation or finding.title


_BUILDERS = {
    POLICY_P10: _explain_p10,
    POLICY_P11: _explain_p11,
    POLICY_P12: _explain_p12,
    POLICY_P13: _explain_p13,
    POLICY_P14: _explain_p14,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _loc(finding: Finding) -> str:
    """Return a 'file:line' location string."""
    if finding.lineno:
        return f"{finding.file}:{finding.lineno}"
    return finding.file or "<unknown>"


def _evidence_value(finding: Finding, prefix: str) -> Optional[str]:
    """Pull a value out of the finding's evidence list by prefix."""
    for ev in finding.evidence:
        if ev.startswith(prefix):
            return ev[len(prefix):].strip()
    return None


def _maybe_llm_polish(text: str, finding: Finding) -> str:
    """Optional local-LLM polish hook.

    Set ``SEMANTIC_TRACE_LLM_COMMAND`` to a local command such as an Ollama
    wrapper. The prompt is sent on stdin unless an argument contains the literal
    ``{prompt}``, in which case that placeholder is replaced. Any failure,
    timeout, or empty response falls back to deterministic text.
    """
    command = os.environ.get("SEMANTIC_TRACE_LLM_COMMAND")
    if not command:
        return text

    prompt = (
        "Rewrite this security finding explanation in one concise paragraph. "
        "Keep the policy id, do not add facts, and do not change severity.\n\n"
        f"Policy: {finding.policy_id}\n"
        f"Title: {finding.title}\n"
        f"Explanation: {text}\n"
    )

    try:
        args = shlex.split(command, posix=os.name != "nt")
        if not args:
            return text

        if any("{prompt}" in arg for arg in args):
            args = [arg.replace("{prompt}", prompt) for arg in args]
            input_text = None
        else:
            input_text = prompt

        completed = subprocess.run(
            args,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return text

    polished = completed.stdout.strip()
    if completed.returncode != 0 or not polished:
        return text
    return " ".join(polished.split())
