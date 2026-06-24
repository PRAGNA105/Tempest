"""Tests for P11 (production values in non-production files)
and P10 value-fact classification.

These tests run against the live demo_app/ fixture and also
construct synthetic examples.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_trace.core.constants import (
    classify_name_semantics,
    classify_value_semantics,
    is_non_prod_path,
)
from semantic_trace.core.models import ValueFact
from semantic_trace.tools import ast_parser, variable_tracker, policy_evaluator, import_graph


# ---------------------------------------------------------------------------
# Unit tests for classification helpers
# ---------------------------------------------------------------------------

class TestNameSemantics(unittest.TestCase):
    def test_prod_name(self):
        self.assertIn("prod", classify_name_semantics("PROD_DB_URL"))

    def test_staging_name(self):
        self.assertIn("non_prod", classify_name_semantics("staging_host"))

    def test_infra_name(self):
        self.assertIn("infra", classify_name_semantics("DB_URL"))

    def test_neutral_name(self):
        self.assertEqual(set(), classify_name_semantics("amount_cents"))


class TestValueSemantics(unittest.TestCase):
    def test_prod_url(self):
        tags = classify_value_semantics(
            "postgresql://prod.company.com:5432/maindb"
        )
        self.assertIn("prod", tags)
        self.assertIn("url", tags)

    def test_localhost(self):
        tags = classify_value_semantics("http://localhost:8080")
        self.assertIn("non_prod", tags)
        self.assertIn("url", tags)

    def test_plain_string(self):
        tags = classify_value_semantics("hello world")
        self.assertEqual(set(), tags)

    def test_api_prod(self):
        tags = classify_value_semantics(
            "https://api.prod.company.com/v2/payments"
        )
        self.assertIn("prod", tags)


class TestPathClassification(unittest.TestCase):
    def test_staging_path(self):
        self.assertTrue(is_non_prod_path("config/staging.py"))

    def test_dev_path(self):
        self.assertTrue(is_non_prod_path("config/dev.py"))

    def test_service_path(self):
        self.assertFalse(is_non_prod_path("services/payment.py"))

    def test_test_path(self):
        self.assertTrue(is_non_prod_path("tests/test_payment.py"))


# ---------------------------------------------------------------------------
# Integration test: P11 on demo_app fixture
# ---------------------------------------------------------------------------

class TestP11DemoApp(unittest.TestCase):
    """P11 should fire for PROD_DB_URL inside config/staging.py."""

    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_p11_found(self):
        p11s = [f for f in self.findings if f.policy_id == "P11"]
        self.assertGreaterEqual(len(p11s), 1, "Expected at least one P11 finding")

    def test_p11_staging_file(self):
        p11s = [f for f in self.findings if f.policy_id == "P11"]
        files = {f.file for f in p11s}
        self.assertIn("config/staging.py", files,
                       "P11 should flag config/staging.py")

    def test_p11_variable_name(self):
        p11s = [f for f in self.findings if f.policy_id == "P11"]
        titles = " ".join(f.title for f in p11s)
        self.assertIn("PROD_DB_URL", titles,
                       "P11 finding should mention PROD_DB_URL")


# ---------------------------------------------------------------------------
# Integration test: P10 on demo_app fixture
# ---------------------------------------------------------------------------

class TestP10DemoApp(unittest.TestCase):
    """P10 should fire for PROD_CACHE_URL (prod name, localhost value)."""

    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_p10_found(self):
        p10s = [f for f in self.findings if f.policy_id == "P10"]
        self.assertGreaterEqual(len(p10s), 1, "Expected at least one P10 finding")

    def test_p10_targets_prod_cache_url(self):
        p10s = [f for f in self.findings if f.policy_id == "P10"]
        symbols = {f.source_node for f in p10s}
        self.assertIn("PROD_CACHE_URL", symbols)

    def test_p10_name_prod_value_nonprod(self):
        """A prod *name* with a prod *value* must NOT be P10 (that is P11)."""
        p10s = [f for f in self.findings if f.policy_id == "P10"]
        flagged = {f.source_node for f in p10s}
        self.assertNotIn("PROD_DB_URL", flagged,
                         "PROD_DB_URL has a prod value — it is P11, not P10")


# ---------------------------------------------------------------------------
# Negative tests: clean_app should not trigger P10 or P11
# ---------------------------------------------------------------------------

class TestP11CleanApp(unittest.TestCase):
    """clean_app should produce zero P10/P11 findings."""

    @classmethod
    def setUpClass(cls):
        clean_root = PROJECT_ROOT / "clean_app"
        cls.pr = ast_parser.scan_project(clean_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_no_p11(self):
        p11s = [f for f in self.findings if f.policy_id == "P11"]
        self.assertEqual(len(p11s), 0,
                         f"clean_app should have no P11 findings, got: {p11s}")

    def test_no_p10(self):
        p10s = [f for f in self.findings if f.policy_id == "P10"]
        self.assertEqual(len(p10s), 0,
                         f"clean_app should have no P10 findings, got: {p10s}")


if __name__ == "__main__":
    unittest.main()
