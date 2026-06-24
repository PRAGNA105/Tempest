"""Tests for external policy configuration."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from semantic_trace.core.constants import classify_value_semantics, is_non_prod_path
from semantic_trace.core.policy_config import load_policy_config


class TestPolicyConfig(unittest.TestCase):
    def test_additional_patterns_extend_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "policy.json"
            config_path.write_text(json.dumps({
                "additional_prod_value_patterns": ["payments\\.corp\\.net"],
                "additional_non_prod_path_tokens": ["qa"],
            }), encoding="utf-8")

            config = load_policy_config(config_path)

        tags = classify_value_semantics(
            "https://payments.corp.net/v1",
            config,
        )
        self.assertIn("prod", tags)
        self.assertIn("url", tags)
        self.assertIn(
            "non_prod",
            classify_value_semantics("http://localhost:8080", config),
        )
        self.assertTrue(is_non_prod_path("config/qa.py", config))


if __name__ == "__main__":
    unittest.main()
