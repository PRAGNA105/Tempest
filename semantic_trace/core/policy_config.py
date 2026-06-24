"""External policy configuration for semantic classification.

The defaults mirror the original constants, but callers can load a small JSON
file to retarget production/non-production patterns without editing code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Union


DEFAULT_PROD_NAME_KEYWORDS: tuple[str, ...] = (
    "prod", "production", "live", "release",
)

DEFAULT_NON_PROD_NAME_KEYWORDS: tuple[str, ...] = (
    "staging", "stage", "dev", "development", "test", "testing",
    "local", "mock", "sandbox", "debug", "dummy", "demo", "tmp",
)

DEFAULT_INFRA_NAME_KEYWORDS: tuple[str, ...] = (
    "db", "database", "url", "endpoint", "host", "api", "cache",
    "queue", "broker", "dsn", "connection", "conn", "uri",
)

DEFAULT_PROD_VALUE_PATTERNS: tuple[str, ...] = (
    r"prod\.",
    r"api\.prod\.",
    r"production",
    r"://[^/]*prod[^/]*\.",
)

DEFAULT_NON_PROD_VALUE_PATTERNS: tuple[str, ...] = (
    r"localhost",
    r"127\.0\.0\.1",
    r"staging\.",
    r"\.local\b",
    r"\.internal\b",
    r"\bdev\.",
    r"\bdemo\.",
    r"example\.com",
    r"placeholder",
    r"TODO",
    r"changeme",
    r"memory://",
)

DEFAULT_URL_PATTERN = r"^(https?|postgresql|mysql|redis|amqp|mongodb|memory)://"

DEFAULT_NON_PROD_PATH_TOKENS: tuple[str, ...] = (
    "staging", "stage", "dev", "development", "test", "tests",
    "testing", "local", "mock", "sandbox", "debug", "demo", "fixture",
    "fixtures", "example", "examples", "tmp",
)


@dataclass(frozen=True)
class PolicyConfig:
    """Configurable keyword and regex sets for policy classification."""

    prod_name_keywords: tuple[str, ...] = DEFAULT_PROD_NAME_KEYWORDS
    non_prod_name_keywords: tuple[str, ...] = DEFAULT_NON_PROD_NAME_KEYWORDS
    infra_name_keywords: tuple[str, ...] = DEFAULT_INFRA_NAME_KEYWORDS
    prod_value_patterns: tuple[str, ...] = DEFAULT_PROD_VALUE_PATTERNS
    non_prod_value_patterns: tuple[str, ...] = DEFAULT_NON_PROD_VALUE_PATTERNS
    url_pattern: str = DEFAULT_URL_PATTERN
    non_prod_path_tokens: tuple[str, ...] = DEFAULT_NON_PROD_PATH_TOKENS


DEFAULT_POLICY_CONFIG = PolicyConfig()


def load_policy_config(path: Union[str, Path]) -> PolicyConfig:
    """Load a JSON policy config, replacing or extending default lists.

    Supported keys replace defaults:
      - prod_name_keywords
      - non_prod_name_keywords
      - infra_name_keywords
      - prod_value_patterns
      - non_prod_value_patterns
      - url_pattern
      - non_prod_path_tokens

    Matching ``additional_*`` keys append to defaults instead, e.g.
    ``additional_prod_value_patterns``.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("policy config must be a JSON object")

    return PolicyConfig(
        prod_name_keywords=_items(
            raw, "prod_name_keywords", "additional_prod_name_keywords",
            DEFAULT_PROD_NAME_KEYWORDS,
        ),
        non_prod_name_keywords=_items(
            raw, "non_prod_name_keywords", "additional_non_prod_name_keywords",
            DEFAULT_NON_PROD_NAME_KEYWORDS,
        ),
        infra_name_keywords=_items(
            raw, "infra_name_keywords", "additional_infra_name_keywords",
            DEFAULT_INFRA_NAME_KEYWORDS,
        ),
        prod_value_patterns=_items(
            raw, "prod_value_patterns", "additional_prod_value_patterns",
            DEFAULT_PROD_VALUE_PATTERNS,
        ),
        non_prod_value_patterns=_items(
            raw, "non_prod_value_patterns", "additional_non_prod_value_patterns",
            DEFAULT_NON_PROD_VALUE_PATTERNS,
        ),
        url_pattern=str(raw.get("url_pattern", DEFAULT_URL_PATTERN)),
        non_prod_path_tokens=_items(
            raw, "non_prod_path_tokens", "additional_non_prod_path_tokens",
            DEFAULT_NON_PROD_PATH_TOKENS,
        ),
    )


def _items(
    raw: dict,
    key: str,
    additional_key: str,
    default: Iterable[str],
) -> tuple[str, ...]:
    """Return replacement list plus optional additions, coerced to strings."""
    if key in raw:
        base = _coerce_list(raw[key], key)
    else:
        base = tuple(default)

    if additional_key in raw:
        base = base + _coerce_list(raw[additional_key], additional_key)

    return base


def _coerce_list(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list of strings")
    return tuple(str(item) for item in value)
