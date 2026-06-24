"""Tests for P12 (multi-hop import chain from non-prod to production sinks).

Runs against the live demo_app/ and clean_app/ fixtures.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure the project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_trace.tools import ast_parser, import_graph, variable_tracker, policy_evaluator
from semantic_trace.tools import path_finder


# ---------------------------------------------------------------------------
# Import graph unit tests
# ---------------------------------------------------------------------------

class TestImportGraph(unittest.TestCase):
    """Verify the import graph built from demo_app."""

    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.graph = import_graph.build(cls.pr)

    def test_nodes_include_key_files(self):
        nodes = set(self.graph.nodes)
        for expected in [
            "config/staging.py",
            "config/aliases.py",
            "data/db_client.py",
            "services/payment.py",
        ]:
            self.assertIn(expected, nodes, f"Missing node: {expected}")

    def test_payment_imports_db_client(self):
        self.assertTrue(
            self.graph.has_edge("services/payment.py", "data/db_client.py"),
            "payment.py should import db_client.py",
        )

    def test_db_client_imports_aliases(self):
        self.assertTrue(
            self.graph.has_edge("data/db_client.py", "config/aliases.py"),
            "db_client.py should import aliases.py",
        )

    def test_aliases_imports_staging(self):
        self.assertTrue(
            self.graph.has_edge("config/aliases.py", "config/staging.py"),
            "aliases.py should import staging.py",
        )


# ---------------------------------------------------------------------------
# Path finder unit tests
# ---------------------------------------------------------------------------

class TestPathFinder(unittest.TestCase):
    """Verify reachability from payment.py to staging.py."""

    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.graph = import_graph.build(cls.pr)

    def test_path_payment_to_staging(self):
        paths = path_finder.find_paths(
            self.graph,
            ["services/payment.py"],
            ["config/staging.py"],
        )
        self.assertGreaterEqual(len(paths), 1, "Expected at least one path")
        # The canonical 4-hop chain
        found_chain = any(
            "services/payment.py" in p and "config/staging.py" in p
            for p in paths
        )
        self.assertTrue(found_chain, f"Expected payment→staging chain, got {paths}")

    def test_no_path_notification_to_staging(self):
        paths = path_finder.find_paths(
            self.graph,
            ["services/notification.py"],
            ["config/staging.py"],
        )
        self.assertEqual(len(paths), 0,
                         "notification.py should NOT reach staging.py")


# ---------------------------------------------------------------------------
# P12 integration tests
# ---------------------------------------------------------------------------

class TestP12DemoApp(unittest.TestCase):
    """P12 should fire for the payment→db_client→aliases→staging chain."""

    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_p12_found(self):
        p12s = [f for f in self.findings if f.policy_id == "P12"]
        self.assertGreaterEqual(len(p12s), 1, "Expected at least one P12 finding")

    def test_p12_chain_includes_payment(self):
        p12s = [f for f in self.findings if f.policy_id == "P12"]
        any_payment = any("services/payment.py" in f.path for f in p12s)
        self.assertTrue(any_payment,
                        "At least one P12 chain should start from payment.py")

    def test_p12_chain_ends_at_prod_config(self):
        p12s = [f for f in self.findings if f.policy_id == "P12"]
        sink_files = set()
        for f in p12s:
            if f.path:
                sink_files.add(f.path[-1])
        self.assertTrue(
            sink_files & {"config/staging.py", "config/aliases.py"},
            f"P12 chains should end at a prod-config file, got sinks: {sink_files}",
        )


class TestP12CleanApp(unittest.TestCase):
    """clean_app should produce zero P12 findings."""

    @classmethod
    def setUpClass(cls):
        clean_root = PROJECT_ROOT / "clean_app"
        cls.pr = ast_parser.scan_project(clean_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_no_p12(self):
        p12s = [f for f in self.findings if f.policy_id == "P12"]
        self.assertEqual(len(p12s), 0,
                         f"clean_app should have no P12 findings, got: {p12s}")


if __name__ == "__main__":
    unittest.main()
