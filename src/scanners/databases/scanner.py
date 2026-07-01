from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from scanners.base import Scanner
from scanners.databases.patterns import (
    DATABASE_HOST_ASSIGNMENT_PATTERN,
    DATABASE_URL_PATTERN,
    TRAILING_PUNCTUATION,
)
from scanners.models import DatabaseFinding
from scanners.traversal import TraversalRules, iter_source_files


class DatabaseScanner(Scanner):
    name = "database_scanner"

    def __init__(self, traversal_rules: TraversalRules | None = None) -> None:
        self.traversal_rules = traversal_rules

    def scan(self, repository_path: Path) -> list[DatabaseFinding]:
        findings: list[DatabaseFinding] = []
        seen: set[tuple[str, int, int, str, str]] = set()

        for source_file in iter_source_files(repository_path, self.traversal_rules):
            for match in DATABASE_URL_PATTERN.finditer(source_file.text):
                raw_url = match.group("url").rstrip(TRAILING_PUNCTUATION)
                parsed = _parse_database_url(raw_url)
                if parsed is None:
                    continue

                line, column = _line_column(source_file.text, match.start("url"))
                key = (source_file.relative_path, line, column, "url", parsed.safe_value)
                if key in seen:
                    continue
                seen.add(key)

                findings.append(
                    DatabaseFinding(
                        id=_finding_id(source_file.relative_path, line, column, parsed.safe_value),
                        value=parsed.safe_value,
                        source_file=source_file.relative_path,
                        line=line,
                        column=column,
                        confidence=_confidence(parsed.host),
                        evidence=parsed.safe_value,
                        database_type=parsed.database_type,
                        host=parsed.host,
                        database_name=parsed.database_name,
                        environment_hint=_environment_hint(parsed.safe_value, parsed.host),
                        metadata={
                            "scanner": self.name,
                            "source": "database_url",
                            "scheme": parsed.scheme,
                            "credentials_redacted": parsed.credentials_redacted,
                        },
                    )
                )

            for match in DATABASE_HOST_ASSIGNMENT_PATTERN.finditer(source_file.text):
                host = match.group("host").rstrip(TRAILING_PUNCTUATION)
                line, column = _line_column(source_file.text, match.start("host"))
                database_type = _infer_database_type(match.group("name"), host)
                key = (source_file.relative_path, line, column, "host", host)
                if key in seen:
                    continue
                seen.add(key)

                findings.append(
                    DatabaseFinding(
                        id=_finding_id(source_file.relative_path, line, column, host),
                        value=host,
                        source_file=source_file.relative_path,
                        line=line,
                        column=column,
                        confidence=_confidence(host),
                        evidence=f"{match.group('name')}={host}",
                        database_type=database_type,
                        host=host,
                        database_name=None,
                        environment_hint=_environment_hint(host, host),
                        metadata={"scanner": self.name, "source": "host_assignment"},
                    )
                )

        return findings


class ParsedDatabaseUrl:
    def __init__(
        self,
        *,
        safe_value: str,
        database_type: str,
        scheme: str,
        host: str | None,
        database_name: str | None,
        credentials_redacted: bool,
    ) -> None:
        self.safe_value = safe_value
        self.database_type = database_type
        self.scheme = scheme
        self.host = host
        self.database_name = database_name
        self.credentials_redacted = credentials_redacted


def _parse_database_url(raw_url: str) -> ParsedDatabaseUrl | None:
    if raw_url.lower().startswith("jdbc:"):
        return _parse_jdbc_url(raw_url)
    return _parse_standard_database_url(raw_url)


def _parse_standard_database_url(raw_url: str) -> ParsedDatabaseUrl | None:
    parsed = urlsplit(raw_url)
    if not parsed.scheme or not parsed.netloc:
        return None

    database_type = _database_type_from_scheme(parsed.scheme)
    safe_netloc, redacted = _safe_netloc(parsed)
    database_name = parsed.path.lstrip("/").split("/", 1)[0] or None

    return ParsedDatabaseUrl(
        safe_value=urlunsplit((parsed.scheme, safe_netloc, parsed.path, parsed.query, parsed.fragment)),
        database_type=database_type,
        scheme=parsed.scheme,
        host=parsed.hostname,
        database_name=database_name,
        credentials_redacted=redacted,
    )


def _parse_jdbc_url(raw_url: str) -> ParsedDatabaseUrl | None:
    match = re.match(r"(?i)^jdbc:(?P<driver>[a-z0-9]+)://(?P<rest>.+)$", raw_url)
    if match is None:
        return None

    driver = match.group("driver").lower()
    rest = match.group("rest")
    host_port, separator, tail = rest.partition("/")
    host = host_port.split(":", 1)[0]
    database_name = None

    if driver == "sqlserver":
        database_match = re.search(r"(?i)(?:databaseName|database)=([^;?]+)", rest)
        if database_match:
            database_name = database_match.group(1)
    elif separator:
        database_name = tail.split("?", 1)[0].split(";", 1)[0] or None

    return ParsedDatabaseUrl(
        safe_value=raw_url,
        database_type=_database_type_from_scheme(driver),
        scheme=f"jdbc:{driver}",
        host=host or None,
        database_name=database_name,
        credentials_redacted=False,
    )


def _safe_netloc(parsed) -> tuple[str, bool]:
    if parsed.username is None and parsed.password is None:
        return parsed.netloc, False

    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port else ""
    return f"<credentials>@{host}{port}", True


def _database_type_from_scheme(value: str) -> str:
    normalized = value.lower()
    if normalized in {"postgres", "postgresql"}:
        return "postgresql"
    if normalized in {"mysql", "mariadb"}:
        return normalized
    if normalized in {"mongodb", "mongodb+srv"}:
        return "mongodb"
    if normalized in {"redis", "rediss"}:
        return "redis"
    if normalized in {"mssql", "sqlserver"}:
        return "sqlserver"
    return normalized


def _infer_database_type(name: str, host: str) -> str:
    haystack = f"{name} {host}".lower()
    for token, database_type in (
        ("postgres", "postgresql"),
        ("postgresql", "postgresql"),
        ("mysql", "mysql"),
        ("mariadb", "mariadb"),
        ("mongo", "mongodb"),
        ("mongodb", "mongodb"),
        ("redis", "redis"),
        ("mssql", "sqlserver"),
        ("sqlserver", "sqlserver"),
    ):
        if token in haystack:
            return database_type
    return "database"


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


def _finding_id(source_file: str, line: int, column: int, value: str) -> str:
    digest = hashlib.sha256(
        f"database:{source_file}:{line}:{column}:{value}".encode("utf-8")
    ).hexdigest()
    return f"database-{digest[:16]}"


def _confidence(host: str | None) -> float:
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return 0.75
    return 0.9


def _environment_hint(value: str, host: str | None) -> str | None:
    haystack = f"{host or ''} {value}".lower()
    hints = (
        ("production", ("production", "prod")),
        ("staging", ("staging", "stage", "stg")),
        ("development", ("development", "dev", "localhost", "127.0.0.1")),
        ("test", ("test", "testing")),
        ("qa", ("qa",)),
    )
    for environment, tokens in hints:
        if any(_contains_token(haystack, token) for token in tokens):
            return environment
    return None


def _contains_token(value: str, token: str) -> bool:
    return re.search(rf"(^|[^a-z0-9]){re.escape(token)}([^a-z0-9]|$)", value) is not None

