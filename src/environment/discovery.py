from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from environment.models import EnvironmentCandidate, EnvironmentName
from scanners import CloudResourceFinding, DatabaseFinding, Finding, URLFinding

ENVIRONMENT_TOKENS: tuple[tuple[EnvironmentName, tuple[str, ...]], ...] = (
    (EnvironmentName.PRODUCTION, ("production", "prod")),
    (EnvironmentName.STAGING, ("staging", "stage", "stg")),
    (EnvironmentName.DEVELOPMENT, ("development", "dev", "localhost", "127.0.0.1")),
    (EnvironmentName.TEST, ("test", "testing")),
    (EnvironmentName.QA, ("qa",)),
)


class EnvironmentDiscovery:
    name = "environment_discovery"

    def discover(self, findings: list[Finding]) -> list[EnvironmentCandidate]:
        candidates: list[EnvironmentCandidate] = []
        seen: set[tuple[str, str]] = set()

        for finding in findings:
            environment = _explicit_environment_hint(finding) or _infer_environment(finding)
            if environment is None:
                continue

            key = (finding.id, environment.value)
            if key in seen:
                continue
            seen.add(key)

            explicit = _explicit_environment_hint(finding) is not None
            confidence = _candidate_confidence(finding, explicit=explicit)
            evidence = _candidate_evidence(finding)
            candidates.append(
                EnvironmentCandidate(
                    id=_candidate_id(finding.id, environment.value),
                    name=environment,
                    source_finding_id=finding.id,
                    source_finding_type=finding.__class__.__name__,
                    source_file=finding.source_file,
                    line=finding.line,
                    column=finding.column,
                    confidence=confidence,
                    evidence=evidence,
                    metadata={
                        "discovery": self.name,
                        "source_scanner": finding.metadata.get("scanner"),
                        "source_confidence": finding.confidence,
                        "signal": "explicit_hint" if explicit else "resource_token",
                    },
                )
            )

        return candidates


def save_environment_candidates_json(
    candidates: list[EnvironmentCandidate], output_path: Path
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [candidate.model_dump(mode="json") for candidate in candidates]
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def _explicit_environment_hint(finding: Finding) -> EnvironmentName | None:
    if isinstance(finding, (URLFinding, DatabaseFinding)) and finding.environment_hint:
        return _environment_from_value(finding.environment_hint)
    return None


def _infer_environment(finding: Finding) -> EnvironmentName | None:
    if isinstance(finding, CloudResourceFinding):
        haystack = " ".join(
            value
            for value in (
                finding.resource_id,
                finding.resource_type,
                finding.value,
                finding.evidence,
            )
            if value
        )
        return _environment_from_value(haystack)

    if isinstance(finding, (URLFinding, DatabaseFinding)):
        haystack = " ".join(
            value
            for value in (
                finding.value,
                finding.evidence,
                getattr(finding, "hostname", None),
                getattr(finding, "host", None),
                getattr(finding, "database_name", None),
            )
            if value
        )
        return _environment_from_value(haystack)

    return None


def _environment_from_value(value: str) -> EnvironmentName | None:
    normalized = value.lower()
    for environment, tokens in ENVIRONMENT_TOKENS:
        if any(_contains_token(normalized, token) for token in tokens):
            return environment
    return None


def _contains_token(value: str, token: str) -> bool:
    return re.search(rf"(^|[^a-z0-9]){re.escape(token)}([^a-z0-9]|$)", value) is not None


def _candidate_confidence(finding: Finding, *, explicit: bool) -> float:
    multiplier = 0.95 if explicit else 0.8
    return round(min(1.0, finding.confidence * multiplier), 3)


def _candidate_evidence(finding: Finding) -> str:
    if finding.evidence:
        return finding.evidence
    return finding.value


def _candidate_id(source_finding_id: str, environment: str) -> str:
    digest = hashlib.sha256(f"environment:{source_finding_id}:{environment}".encode()).hexdigest()
    return f"environment-{digest[:16]}"
