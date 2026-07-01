from __future__ import annotations

import re


DATABASE_URL_PATTERN = re.compile(
    r"\b(?P<url>(?:(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|mssql|sqlserver)://|jdbc:[a-z0-9]+://)[^\s<>'\"`\\]+)",
    re.IGNORECASE,
)

DATABASE_HOST_ASSIGNMENT_PATTERN = re.compile(
    r"""(?ix)
    \b(?P<name>
        [a-z0-9_.-]*
        (?:
            database|db|postgres|postgresql|mysql|mariadb|mongo|mongodb|redis|mssql|sqlserver
        )
        [a-z0-9_.-]*
        (?:host|endpoint|server)
        [a-z0-9_.-]*
    )
    \b
    \s*[:=]\s*
    (?P<quote>["'])?
    (?P<host>[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(?::[0-9]{2,5})?)
    (?P=quote)?
    """,
)

TRAILING_PUNCTUATION = ".,;:!?)\\]}"

