"""Skills registry — maps the five demo policies to deterministic tools.

The orchestrator consults this registry to describe, in human terms, which
"skill" it is exercising for each policy. Detection itself stays fully
deterministic; this module only carries metadata + a stable ordering so the
agent trace reads as an intentional plan rather than a hardcoded dump.

Interface:
    all_skills() -> list[Skill]
    skill_for(policy_id) -> Skill | None
    policies_for_goal(goal) -> list[str]
"""

from __future__ import annotations

from dataclasses import dataclass

from semantic_trace.core.constants import (
    POLICY_P10,
    POLICY_P11,
    POLICY_P12,
    POLICY_P13,
    POLICY_P14,
)


@dataclass(frozen=True)
class Skill:
    """One detection capability the agent can choose to apply."""

    policy_id: str
    name: str
    question: str          # the security question this skill answers
    tools: list[str]       # deterministic tools the skill relies on


# Ordered so the trace flows value-facts -> reachability -> taint -> aliases.
_SKILLS: list[Skill] = [
    Skill(
        policy_id=POLICY_P10,
        name="Prod-named placeholder detector",
        question="Does any production-named variable actually hold a local/placeholder value?",
        tools=["ast_parser", "variable_tracker"],
    ),
    Skill(
        policy_id=POLICY_P11,
        name="Prod-value-in-nonprod-file detector",
        question="Does a non-production file hardcode a production resource?",
        tools=["ast_parser", "variable_tracker"],
    ),
    Skill(
        policy_id=POLICY_P12,
        name="Import-chain reachability tracer",
        question="Can non-production code reach a production sink through imports?",
        tools=["ast_parser", "import_graph", "path_finder"],
    ),
    Skill(
        policy_id=POLICY_P13,
        name="Dynamic-endpoint taint tracker",
        question="Is a production endpoint assembled at runtime from harmless-looking fragments?",
        tools=["ast_parser", "variable_tracker"],
    ),
    Skill(
        policy_id=POLICY_P14,
        name="Aliased-identifier resolver",
        question="Is a production endpoint hidden behind an innocent dictionary key?",
        tools=["ast_parser", "variable_tracker"],
    ),
]

_BY_POLICY = {s.policy_id: s for s in _SKILLS}


def all_skills() -> list[Skill]:
    """Return every registered skill in trace order."""
    return list(_SKILLS)


def skill_for(policy_id: str) -> Skill | None:
    """Return the skill responsible for *policy_id*, or None."""
    return _BY_POLICY.get(policy_id)


def policies_for_goal(goal: str) -> list[str]:
    """Select which policies to evaluate for *goal*.

    The demo goal is broad ("detect non-production reach into production"),
    so all five policies apply. If the goal names a specific policy id
    (e.g. "check P12"), only that policy is selected.
    """
    upper = goal.upper()
    named = [s.policy_id for s in _SKILLS if s.policy_id in upper]
    if named:
        return named
    return [s.policy_id for s in _SKILLS]
