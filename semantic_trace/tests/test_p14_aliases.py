"""Tests for P14 (aliased production identifiers).

Verifies that dict-literal aliases mapping innocent keys to production URLs
are detected on demo_app and absent on clean_app.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_trace.tools import (
    ast_parser,
    import_graph,
    policy_evaluator,
    variable_tracker,
)


# ---------------------------------------------------------------------------
# Alias-fact extraction (variable tracker)
# ---------------------------------------------------------------------------

class TestAliasFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.st = variable_tracker.resolve(cls.pr)

    def test_aliases_populated(self):
        keys = {a.alias_name for a in self.st.aliases}
        self.assertIn("payments", keys)
        self.assertIn("notify", keys)

    def test_alias_resolves_to_prod_url(self):
        payments = next(a for a in self.st.aliases if a.alias_name == "payments")
        self.assertIn("api.prod.company.com", payments.original_symbol)
        self.assertEqual(payments.container, "ENDPOINT_MAP")

    def test_alias_consumer_populated(self):
        uses = [
            use for use in self.st.alias_uses
            if use.container == "ENDPOINT_MAP" and use.alias_name == "payments"
        ]
        self.assertTrue(uses, "Expected a literal ENDPOINT_MAP payments consumer")
        self.assertTrue(any(use.file == "services/payment.py" for use in uses))


# ---------------------------------------------------------------------------
# P14 integration: demo_app (positive)
# ---------------------------------------------------------------------------

class TestP14DemoApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_p14_found(self):
        p14s = [f for f in self.findings if f.policy_id == "P14"]
        self.assertGreaterEqual(len(p14s), 2,
                                "Expected P14 findings for payments and notify")

    def test_p14_keys(self):
        p14s = [f for f in self.findings if f.policy_id == "P14"]
        keys = {f.source_node for f in p14s}
        self.assertIn("payments", keys)
        self.assertIn("notify", keys)

    def test_p14_in_aliases_file(self):
        p14s = [f for f in self.findings if f.policy_id == "P14"]
        files = {f.file for f in p14s}
        self.assertEqual(files, {"config/aliases.py"})

    def test_p14_payments_includes_consumer_evidence(self):
        payments = next(
            f for f in self.findings
            if f.policy_id == "P14" and f.source_node == "payments"
        )
        evidence = "\n".join(payments.evidence)
        self.assertIn("Consumer: services/payment.py", evidence)
        self.assertIn("aliases.ENDPOINT_MAP.get", evidence)


# ---------------------------------------------------------------------------
# P14 negative: clean_app
# ---------------------------------------------------------------------------

class TestP14CleanApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clean_root = PROJECT_ROOT / "clean_app"
        cls.pr = ast_parser.scan_project(clean_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_no_p14(self):
        # clean_app's ENDPOINT_MAP values are localhost — no prod aliases.
        p14s = [f for f in self.findings if f.policy_id == "P14"]
        self.assertEqual(len(p14s), 0,
                         f"clean_app should have no P14 findings, got: {p14s}")


if __name__ == "__main__":
    unittest.main()
