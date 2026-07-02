from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

from scanners.base import Scanner
from scanners.models import URLFinding
from scanners.traversal import TraversalRules, iter_source_files


URL_PATTERN = re.compile(r"\bhttps?://[^\s<>'\"`\\]+", re.IGNORECASE)
TRAILING_PUNCTUATION = ".,;:!?)\\]}"


class URLScanner(Scanner):
    name = "url_scanner"

    def __init__(self, traversal_rules: TraversalRules | None = None) -> None:
        self.traversal_rules = traversal_rules

    def scan(self, repository_path: Path) -> list[URLFinding]:
        findings: list[URLFinding] = []
        for source_file in iter_source_files(repository_path, self.traversal_rules):
            for match in URL_PATTERN.finditer(source_file.text):
                raw_url = _normalize_url_match(match.group(0))
                parsed = urlparse(raw_url)
                if not parsed.scheme or not parsed.netloc:
                    continue

                line, column = _line_column(source_file.text, match.start())
                findings.append(
                    URLFinding(
                        id=_finding_id(source_file.relative_path, line, column, raw_url),
                        value=raw_url,
                        source_file=source_file.relative_path,
                        line=line,
                        column=column,
                        confidence=_confidence(parsed.hostname),
                        evidence=raw_url,
                        url=raw_url,
                        scheme=parsed.scheme.lower(),
                        hostname=parsed.hostname,
                        environment_hint=_environment_hint(raw_url, parsed.hostname),
                        metadata={"scanner": self.name},
                    )
                )
        return findings


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


def _normalize_url_match(raw_url: str) -> str:
    cleaned = raw_url.split("](", 1)[0]
    return cleaned.rstrip(TRAILING_PUNCTUATION)


def _finding_id(source_file: str, line: int, column: int, url: str) -> str:
    digest = hashlib.sha256(f"url:{source_file}:{line}:{column}:{url}".encode("utf-8")).hexdigest()
    return f"url-{digest[:16]}"


def _confidence(hostname: str | None) -> float:
    if hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return 0.7
    return 0.95


def _environment_hint(url: str, hostname: str | None) -> str | None:
    haystack = f"{hostname or ''} {url}".lower()
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
