"""Tests for the brain: orchestrator loop, skills registry, explainer."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_trace.brain import explainer, orchestrator, skills
from semantic_trace.__main__ import _print_ranked_findings


# ---------------------------------------------------------------------------
# Skills registry
# ---------------------------------------------------------------------------

class TestSkills(unittest.TestCase):
    def test_all_five_policies_registered(self):
        ids = {s.policy_id for s in skills.all_skills()}
        self.assertEqual(ids, {"P10", "P11", "P12", "P13", "P14"})

    def test_broad_goal_selects_all(self):
        self.assertEqual(
            set(skills.policies_for_goal("detect everything")),
            {"P10", "P11", "P12", "P13", "P14"},
        )

    def test_named_policy_goal_narrows(self):
        self.assertEqual(skills.policies_for_goal("only check P12"), ["P12"])


# ---------------------------------------------------------------------------
# Orchestrator loop
# ---------------------------------------------------------------------------

class TestOrchestratorDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = orchestrator.run("", PROJECT_ROOT / "demo_app")

    def test_trace_has_all_phases(self):
        phases = {s.phase for s in self.result.trace}
        for expected in ["Goal", "Thought", "Tool", "Observation", "Decision"]:
            self.assertIn(expected, phases)

    def test_trace_is_ordered_goal_first_decision_last(self):
        self.assertEqual(self.result.trace[0].phase, "Goal")
        self.assertEqual(self.result.trace[-1].phase, "Decision")

    def test_all_policies_emitted(self):
        ids = {f.policy_id for f in self.result.findings}
        self.assertEqual(ids, {"P10", "P11", "P12", "P13", "P14"})

    def test_findings_have_explanations(self):
        for f in self.result.findings:
            self.assertTrue(f.explanation.startswith(f.policy_id),
                            f"explanation should be enriched for {f.id}")

    def test_findings_are_ranked_by_severity(self):
        severities = [f.severity for f in self.result.findings]
        self.assertEqual(severities, sorted(
            severities,
            key={"critical": 0, "high": 1, "medium": 2, "low": 3}.get,
        ))

    def test_summary_flags_not_clean(self):
        self.assertIn("NOT clean", self.result.summary)


class TestOrchestratorClean(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = orchestrator.run("", PROJECT_ROOT / "clean_app")

    def test_no_findings(self):
        self.assertEqual(len(self.result.findings), 0)

    def test_summary_flags_clean(self):
        self.assertIn("clean", self.result.summary.lower())


# ---------------------------------------------------------------------------
# Explainer
# ---------------------------------------------------------------------------

class TestExplainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = orchestrator.run("", PROJECT_ROOT / "demo_app")

    def test_explain_is_deterministic(self):
        f = self.result.findings[0]
        a = explainer.explain(f)
        b = explainer.explain(f)
        self.assertEqual(a, b)

    def test_explain_llm_flag_falls_back(self):
        f = self.result.findings[0]
        self.assertEqual(
            explainer.explain(f, use_llm=False),
            explainer.explain(f, use_llm=True),
        )


class TestReportFormatting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = orchestrator.run("", PROJECT_ROOT / "demo_app")

    def test_p12_findings_group_under_shared_sink(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            _print_ranked_findings(self.result.findings)
        text = out.getvalue()
        self.assertIn("[P12] Import chains to production sink:", text)
        self.assertIn("Chains:", text)


if __name__ == "__main__":
    unittest.main()
