from __future__ import annotations

import hashlib
import json
from pathlib import Path

from boundary.models import ProductionBoundaryCandidate, ProductionBoundaryType
from environment.models import EnvironmentCandidate, EnvironmentName
from scanners.models import CloudResourceFinding, DatabaseFinding, Finding, URLFinding

_FINDING_TYPE_TO_BOUNDARY_TYPE: dict[str, ProductionBoundaryType] = {
    "URLFinding": ProductionBoundaryType.EXTERNAL_URL,
    "DatabaseFinding": ProductionBoundaryType.EXTERNAL_DATABASE,
    "CloudResourceFinding": ProductionBoundaryType.CLOUD_RESOURCE,
}

_LOCALHOST_HOSTS: frozenset[str] = frozenset(
    {"localhost", "127.0.0.1", "0.0.0.0", "::1"}  # noqa: S104 - not a bind, just a match set.
)

_INTERNAL_SUFFIXES: tuple[str, ...] = (".local", ".internal", ".localhost")


class ProductionBoundaryDiscovery:
    """Derives production boundary candidates from environment candidates and findings."""

    name = "production_boundary_discovery"

    def discover(
        self,
        candidates: list[EnvironmentCandidate],
        findings: list[Finding],
    ) -> list[ProductionBoundaryCandidate]:
        findings_by_id = {finding.id: finding for finding in findings}
        results: list[ProductionBoundaryCandidate] = []
        seen: set[str] = set()

        for candidate in candidates:
            if candidate.name != EnvironmentName.PRODUCTION:
                continue

            finding = findings_by_id.get(candidate.source_finding_id)
            if finding is None:
                continue

            boundary_type = _FINDING_TYPE_TO_BOUNDARY_TYPE.get(candidate.source_finding_type)
            if boundary_type is None:
                continue

            boundary_id = _boundary_id(candidate.id, finding.id)
            if boundary_id in seen:
                continue
            seen.add(boundary_id)

            results.append(
                ProductionBoundaryCandidate(
                    id=boundary_id,
                    boundary_type=boundary_type,
                    source_environment_id=candidate.id,
                    source_finding_id=finding.id,
                    source_finding_type=candidate.source_finding_type,
                    source_file=finding.source_file,
                    line=finding.line,
                    column=finding.column,
                    externally_reachable=_is_externally_reachable(finding),
                    confidence=_boundary_confidence(candidate),
                    evidence=_boundary_evidence(finding, candidate),
                    metadata={
                        "discovery": self.name,
                        "source_environment_name": candidate.name.value,
                        "source_environment_confidence": candidate.confidence,
                        "source_scanner": candidate.metadata.get("source_scanner"),
                    },
                )
            )

        return results


def save_boundary_candidates_json(
    candidates: list[ProductionBoundaryCandidate], output_path: Path
) -> Path:
    """Persist production boundary candidates as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [candidate.model_dump(mode="json") for candidate in candidates]
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def _is_externally_reachable(finding: Finding) -> bool:
    """Determine if a finding represents an externally reachable resource."""
    if isinstance(finding, URLFinding):
        return _is_external_hostname(finding.hostname)

    if isinstance(finding, DatabaseFinding):
        return _is_external_hostname(finding.host)

    if isinstance(finding, CloudResourceFinding):
        # Cloud resources are network-accessible by definition.
        return True

    return False


def _is_external_hostname(hostname: str | None) -> bool:
    """Return True unless the hostname is clearly localhost or internal."""
    if not hostname:
        return False
    normalized = hostname.lower().strip()
    if normalized in _LOCALHOST_HOSTS:
        return False
    if any(normalized.endswith(suffix) for suffix in _INTERNAL_SUFFIXES):
        return False
    return True


def _boundary_confidence(candidate: EnvironmentCandidate) -> float:
    """Derive boundary confidence from the environment candidate confidence."""
    return round(min(1.0, candidate.confidence * 0.95), 3)


def _boundary_evidence(finding: Finding, candidate: EnvironmentCandidate) -> str:
    """Compose boundary evidence from finding and candidate."""
    if finding.evidence:
        return finding.evidence
    if candidate.evidence:
        return candidate.evidence
    return finding.value


def _boundary_id(environment_id: str, finding_id: str) -> str:
    """Generate a deterministic stable boundary ID."""
    digest = hashlib.sha256(f"boundary:{environment_id}:{finding_id}".encode()).hexdigest()
    return f"boundary-{digest[:16]}"
