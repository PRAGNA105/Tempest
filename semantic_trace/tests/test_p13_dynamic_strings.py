"""Tests for P13 (dynamic string construction of production endpoints).

Verifies the lightweight intra-file taint resolver (string concatenation,
f-strings, name resolution) and the P13 policy rule on both fixtures.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_trace.core.models import AssignmentFact, ImportFact, ParseResult
from semantic_trace.tools import (
    ast_parser,
    import_graph,
    policy_evaluator,
    variable_tracker,
)


def _resolve_source(src: str) -> dict:
    """Parse a snippet and return {symbol: ValueFact} for its assignments."""
    tree = ast.parse(src)
    assignments = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            assignments.append(AssignmentFact(
                file="snippet.py",
                target=node.targets[0].id,
                value_repr=ast.unparse(node.value),
                value_node=node.value,
                lineno=node.lineno,
            ))
    pr = ParseResult(files={"snippet.py": tree}, assignments=assignments)
    st = variable_tracker.resolve(pr)
    return {vf.symbol: vf for vf in st.values}


def _assignment_facts(file: str, tree: ast.Module) -> list[AssignmentFact]:
    facts: list[AssignmentFact] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            facts.append(AssignmentFact(
                file=file,
                target=node.targets[0].id,
                value_repr=ast.unparse(node.value),
                value_node=node.value,
                lineno=node.lineno,
            ))
    return facts


# ---------------------------------------------------------------------------
# Unit tests for the taint resolver
# ---------------------------------------------------------------------------

class TestTaintResolver(unittest.TestCase):
    def test_binop_concat(self):
        vfs = _resolve_source(
            'BASE = "postgresql://"\n'
            'HOST = "prod.company.com"\n'
            'conn = BASE + HOST + "/maindb"\n'
        )
        conn = vfs["conn"]
        self.assertTrue(conn.is_constructed)
        self.assertEqual(conn.resolved_value, "postgresql://prod.company.com/maindb")
        self.assertIn("prod", conn.value_semantics)
        self.assertIn("url", conn.value_semantics)

    def test_fstring_resolution(self):
        vfs = _resolve_source(
            'HOST = "prod.company.com"\n'
            'url = f"https://{HOST}/v2/pay"\n'
        )
        url = vfs["url"]
        self.assertTrue(url.is_constructed)
        self.assertEqual(url.resolved_value, "https://prod.company.com/v2/pay")
        self.assertIn("prod", url.value_semantics)

    def test_unresolvable_call_returns_none(self):
        vfs = _resolve_source('x = some_func() + "/maindb"\n')
        self.assertIsNone(vfs["x"].resolved_value)

    def test_plain_literal_not_constructed(self):
        vfs = _resolve_source('x = "postgresql://prod.company.com/maindb"\n')
        self.assertFalse(vfs["x"].is_constructed)

    def test_cross_file_imported_fragment_resolution(self):
        host_tree = ast.parse('HOST = "prod.company.com"\n')
        client_tree = ast.parse(
            "from demo_app.config.hosts import HOST\n"
            'BASE = "postgresql://"\n'
            'conn = BASE + HOST + "/maindb"\n'
        )
        pr = ParseResult(
            files={
                "config/hosts.py": host_tree,
                "data/client.py": client_tree,
            },
            imports=[
                ImportFact(
                    source_file="data/client.py",
                    module="demo_app.config.hosts",
                    names=["HOST"],
                    lineno=1,
                )
            ],
            assignments=(
                _assignment_facts("config/hosts.py", host_tree)
                + _assignment_facts("data/client.py", client_tree)
            ),
        )
        st = variable_tracker.resolve(pr)
        conn = next(vf for vf in st.values if vf.symbol == "conn")
        self.assertTrue(conn.is_constructed)
        self.assertEqual(conn.resolved_value, "postgresql://prod.company.com/maindb")
        graph = import_graph.build(pr)
        findings = policy_evaluator.evaluate(pr, st, graph)
        self.assertTrue(any(f.policy_id == "P13" for f in findings))


# ---------------------------------------------------------------------------
# P13 integration: demo_app (positive)
# ---------------------------------------------------------------------------

class TestP13DemoApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        demo_root = PROJECT_ROOT / "demo_app"
        cls.pr = ast_parser.scan_project(demo_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_p13_found(self):
        p13s = [f for f in self.findings if f.policy_id == "P13"]
        self.assertGreaterEqual(len(p13s), 1, "Expected at least one P13 finding")

    def test_p13_targets_conn_str(self):
        p13s = [f for f in self.findings if f.policy_id == "P13"]
        symbols = {f.source_node for f in p13s}
        self.assertIn("conn_str", symbols,
                      "P13 should flag the constructed conn_str")

    def test_p13_in_db_client(self):
        p13s = [f for f in self.findings if f.policy_id == "P13"]
        files = {f.file for f in p13s}
        self.assertIn("data/db_client.py", files)

    def test_p13_no_single_literal_is_full_url(self):
        # The whole point of P13: the resolved URL is prod, but it is never a
        # single literal — assembled from BASE + HOST + "/maindb".
        p13 = next(f for f in self.findings if f.policy_id == "P13")
        joined = " ".join(p13.evidence)
        self.assertIn("postgresql://prod.company.com/maindb", joined)


# ---------------------------------------------------------------------------
# P13 negative: clean_app
# ---------------------------------------------------------------------------

class TestP13CleanApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clean_root = PROJECT_ROOT / "clean_app"
        cls.pr = ast_parser.scan_project(clean_root)
        cls.st = variable_tracker.resolve(cls.pr)
        cls.graph = import_graph.build(cls.pr)
        cls.findings = policy_evaluator.evaluate(cls.pr, cls.st, cls.graph)

    def test_no_p13(self):
        # clean_app's conn_str resolves to staging.internal — non-production.
        p13s = [f for f in self.findings if f.policy_id == "P13"]
        self.assertEqual(len(p13s), 0,
                         f"clean_app should have no P13 findings, got: {p13s}")


if __name__ == "__main__":
    unittest.main()
