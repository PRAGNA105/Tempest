"""Constants for production/non-production semantic classification.

All detection heuristics for the demo are defined here so policy rules
and the variable tracker share a single source of truth. The default values
come from :mod:`semantic_trace.core.policy_config`, and every classifier can
optionally receive a loaded ``PolicyConfig`` for retargeted scans.
"""

from __future__ import annotations

import re

from semantic_trace.core.policy_config import (
    DEFAULT_POLICY_CONFIG,
    PolicyConfig,
)

# ---------------------------------------------------------------------------
# Policy identifiers
# ---------------------------------------------------------------------------

POLICY_P10 = "P10"  # Prod-named variables masking placeholders
POLICY_P11 = "P11"  # Production URLs inside non-production configuration
POLICY_P12 = "P12"  # Multi-hop import chain from non-prod to prod sinks
POLICY_P13 = "P13"  # Dynamic string construction of production endpoints
POLICY_P14 = "P14"  # Aliased production identifiers

ALL_POLICIES = [POLICY_P10, POLICY_P11, POLICY_P12, POLICY_P13, POLICY_P14]

# ---------------------------------------------------------------------------
# Name-semantic keywords  (applied to variable/file/function names)
# ---------------------------------------------------------------------------

# Keywords that suggest *production* intent in a name
PROD_NAME_KEYWORDS: set[str] = set(DEFAULT_POLICY_CONFIG.prod_name_keywords)

# Keywords that suggest *non-production* intent in a name
NON_PROD_NAME_KEYWORDS: set[str] = set(
    DEFAULT_POLICY_CONFIG.non_prod_name_keywords
)

# Infrastructure-role keywords (neutral — they gain meaning from context)
INFRA_NAME_KEYWORDS: set[str] = set(DEFAULT_POLICY_CONFIG.infra_name_keywords)

# ---------------------------------------------------------------------------
# Value-semantic patterns  (applied to string literal *values*)
# ---------------------------------------------------------------------------

# Patterns that mark a string value as *production*
PROD_VALUE_PATTERNS: list[re.Pattern] = [
    re.compile(pattern, re.I)
    for pattern in DEFAULT_POLICY_CONFIG.prod_value_patterns
]

# Patterns that mark a string value as *non-production / placeholder*
NON_PROD_VALUE_PATTERNS: list[re.Pattern] = [
    re.compile(pattern, re.I)
    for pattern in DEFAULT_POLICY_CONFIG.non_prod_value_patterns
]

# URL-ish value pattern (to know a string is some kind of endpoint)
URL_PATTERN: re.Pattern = re.compile(
    DEFAULT_POLICY_CONFIG.url_pattern
)

# ---------------------------------------------------------------------------
# File-path classification helpers
# ---------------------------------------------------------------------------

# If any of these tokens appear in a file's relative path, it is
# considered *non-production context*.
NON_PROD_PATH_TOKENS: set[str] = set(
    DEFAULT_POLICY_CONFIG.non_prod_path_tokens
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def classify_name_semantics(
    name: str,
    config: PolicyConfig | None = None,
) -> set[str]:
    """Return semantic tags for an identifier name.

    >>> sorted(classify_name_semantics("PROD_DB_URL"))
    ['infra', 'prod']
    """
    config = config or DEFAULT_POLICY_CONFIG
    lower = name.lower()
    parts = set(re.split(r"[_.\-/]", lower))
    tags: set[str] = set()
    if parts & set(config.prod_name_keywords):
        tags.add("prod")
    if parts & set(config.non_prod_name_keywords):
        tags.add("non_prod")
    if parts & set(config.infra_name_keywords):
        tags.add("infra")
    return tags


def classify_value_semantics(
    value: str,
    config: PolicyConfig | None = None,
) -> set[str]:
    """Return semantic tags for a string value.

    >>> sorted(classify_value_semantics("postgresql://prod.company.com:5432/maindb"))
    ['prod', 'url']
    """
    config = config or DEFAULT_POLICY_CONFIG
    tags: set[str] = set()
    if re.compile(config.url_pattern).search(value):
        tags.add("url")
    for pat in _compile_patterns(config.prod_value_patterns):
        if pat.search(value):
            tags.add("prod")
            break
    for pat in _compile_patterns(config.non_prod_value_patterns):
        if pat.search(value):
            tags.add("non_prod")
            break
    return tags


def is_non_prod_path(
    rel_path: str,
    config: PolicyConfig | None = None,
) -> bool:
    """Return True if *rel_path* contains a non-production path token.

    >>> is_non_prod_path("config/staging.py")
    True
    >>> is_non_prod_path("services/payment.py")
    False
    """
    config = config or DEFAULT_POLICY_CONFIG
    parts = set(re.split(r"[_.\-/\\\\]", rel_path.lower()))
    return bool(parts & set(config.non_prod_path_tokens))


def _compile_patterns(patterns: tuple[str, ...]) -> list[re.Pattern]:
    """Compile configured regex patterns case-insensitively."""
    return [re.compile(pattern, re.I) for pattern in patterns]
