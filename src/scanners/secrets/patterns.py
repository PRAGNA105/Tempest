from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: Pattern[str]
    value_group: str = "value"
    confidence: float = 0.85
    min_entropy: float | None = None


SECRET_PATTERNS = (
    SecretPattern(
        name="aws_access_key_id",
        regex=re.compile(r"\b(?P<value>(?:AKIA|ASIA)[A-Z0-9]{16})\b"),
        confidence=0.95,
    ),
    SecretPattern(
        name="private_key",
        regex=re.compile(
            r"-----BEGIN (?P<value>(?:RSA |EC |OPENSSH )?PRIVATE KEY)-----",
            re.IGNORECASE,
        ),
        confidence=0.95,
    ),
    SecretPattern(
        name="generic_secret_assignment",
        regex=re.compile(
            r"""(?ix)
            \b(?P<name>
                [a-z0-9_.-]*
                (?:secret|token|api[_-]?key|password|private[_-]?key|access[_-]?key)
                [a-z0-9_.-]*
            )
            \b
            \s*[:=]\s*
            (?P<quote>["'])?
            (?P<value>[a-z0-9_./+=:@-]{12,})
            (?P=quote)?
            """,
        ),
        confidence=0.8,
        min_entropy=3.0,
    ),
)

PLACEHOLDER_VALUES = {
    "changeme",
    "change_me",
    "example",
    "example_secret",
    "fake",
    "fake_secret",
    "placeholder",
    "redacted",
    "secret",
    "test",
    "todo",
    "your_api_key",
    "your_secret",
}

