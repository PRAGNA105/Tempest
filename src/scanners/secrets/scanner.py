from __future__ import annotations

import hashlib
from pathlib import Path
from re import Match

from scanners.base import Scanner
from scanners.models import SecretFinding
from scanners.secrets.entropy import shannon_entropy
from scanners.secrets.patterns import PLACEHOLDER_VALUES, SECRET_PATTERNS, SecretPattern
from scanners.traversal import TraversalRules, iter_source_files


class SecretScanner(Scanner):
    name = "secret_scanner"

    def __init__(self, traversal_rules: TraversalRules | None = None) -> None:
        self.traversal_rules = traversal_rules

    def scan(self, repository_path: Path) -> list[SecretFinding]:
        findings: list[SecretFinding] = []
        seen: set[tuple[str, int, int, str]] = set()

        for source_file in iter_source_files(repository_path, self.traversal_rules):
            for pattern in SECRET_PATTERNS:
                for match in pattern.regex.finditer(source_file.text):
                    if _is_unquoted_call_value(pattern, match, source_file.text):
                        continue

                    raw_secret = _raw_secret(pattern, match)
                    normalized = _normalize_secret(raw_secret)
                    if not _is_candidate_secret(normalized):
                        continue
                    if pattern.name == "generic_secret_assignment" and _is_provider_specific(normalized):
                        continue

                    entropy = shannon_entropy(normalized)
                    if pattern.min_entropy is not None and entropy < pattern.min_entropy:
                        continue

                    line, column = _line_column(source_file.text, match.start(pattern.value_group))
                    key = (source_file.relative_path, line, column, pattern.name)
                    if key in seen:
                        continue
                    seen.add(key)

                    findings.append(
                        SecretFinding(
                            id=_finding_id(source_file.relative_path, line, column, pattern.name),
                            value=_redact(normalized),
                            source_file=source_file.relative_path,
                            line=line,
                            column=column,
                            confidence=_confidence(pattern, entropy),
                            evidence=_evidence(pattern, match, normalized),
                            secret_type=pattern.name,
                            entropy=round(entropy, 3),
                            metadata={
                                "scanner": self.name,
                                "fingerprint": _fingerprint(normalized),
                                "value_length": len(normalized),
                            },
                        )
                    )

        return findings


def _raw_secret(pattern: SecretPattern, match: Match[str]) -> str:
    return match.group(pattern.value_group)


def _normalize_secret(value: str) -> str:
    return value.strip().strip("\"'")


def _is_unquoted_call_value(pattern: SecretPattern, match: Match[str], text: str) -> bool:
    if pattern.name != "generic_secret_assignment":
        return False
    if match.groupdict().get("quote"):
        return False

    end = match.end(pattern.value_group)
    return end < len(text) and text[end] == "("


def _is_candidate_secret(value: str) -> bool:
    if len(value) < 8:
        return False
    lowered = value.lower()
    if lowered in PLACEHOLDER_VALUES:
        return False
    if lowered.startswith(("http://", "https://")):
        return False
    return True


def _is_provider_specific(value: str) -> bool:
    return len(value) == 20 and value.startswith(("AKIA", "ASIA"))


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


def _finding_id(source_file: str, line: int, column: int, secret_type: str) -> str:
    digest = hashlib.sha256(
        f"secret:{source_file}:{line}:{column}:{secret_type}".encode("utf-8")
    ).hexdigest()
    return f"secret-{digest[:16]}"


def _confidence(pattern: SecretPattern, entropy: float) -> float:
    if entropy >= 4.0:
        return min(1.0, pattern.confidence + 0.05)
    return pattern.confidence


def _evidence(pattern: SecretPattern, match: Match[str], value: str) -> str:
    if pattern.name == "generic_secret_assignment" and "name" in match.groupdict():
        return f"{match.group('name')}={_redact(value)}"
    return _redact(value)


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:4]}...{value[-4:]}"


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
