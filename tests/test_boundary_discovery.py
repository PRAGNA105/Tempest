import json

from boundary import (
    ProductionBoundaryDiscovery,
    ProductionBoundaryType,
    save_boundary_candidates_json,
)
from environment import EnvironmentCandidate, EnvironmentName
from scanners import (
    CloudProvider,
    CloudResourceFinding,
    DatabaseFinding,
    URLFinding,
)


def _make_url_finding(
    finding_id="url-1",
    hostname="api.prod.example.com",
    environment_hint="production",
):
    return URLFinding(
        id=finding_id,
        value=f"https://{hostname}",
        source_file="settings.py",
        line=10,
        column=14,
        confidence=0.95,
        evidence=f"https://{hostname}",
        url=f"https://{hostname}",
        hostname=hostname,
        environment_hint=environment_hint,
        metadata={"scanner": "url_scanner"},
    )


def _make_database_finding(
    finding_id="db-1",
    host="prod-db.example.com",
    environment_hint="production",
):
    return DatabaseFinding(
        id=finding_id,
        value=f"postgresql://{host}/app",
        source_file="config.py",
        line=5,
        column=20,
        confidence=0.9,
        evidence=f"postgresql://{host}/app",
        database_type="postgresql",
        host=host,
        database_name="app",
        environment_hint=environment_hint,
        metadata={"scanner": "database_scanner"},
    )


def _make_cloud_finding(finding_id="cloud-1", resource_id="prod-worker"):
    return CloudResourceFinding(
        id=finding_id,
        value=f"arn:aws:lambda:us-east-1:123456789012:function:{resource_id}",
        source_file="infra.tf",
        line=4,
        column=20,
        confidence=0.95,
        evidence=f"arn:aws:lambda:us-east-1:123456789012:function:{resource_id}",
        provider=CloudProvider.AWS,
        resource_type="lambda_function",
        resource_id=resource_id,
        region="us-east-1",
        metadata={"scanner": "cloud_resource_scanner"},
    )


def _make_environment_candidate(
    finding,
    env_name=EnvironmentName.PRODUCTION,
    candidate_id="env-1",
):
    return EnvironmentCandidate(
        id=candidate_id,
        name=env_name,
        source_finding_id=finding.id,
        source_finding_type=finding.__class__.__name__,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        confidence=0.902,
        evidence=finding.evidence or finding.value,
        metadata={
            "discovery": "environment_discovery",
            "source_scanner": finding.metadata.get("scanner"),
            "source_confidence": finding.confidence,
            "signal": "explicit_hint",
        },
    )


def test_boundary_discovery_produces_external_url_from_production_candidate():
    url_finding = _make_url_finding()
    candidate = _make_environment_candidate(url_finding)

    results = ProductionBoundaryDiscovery().discover([candidate], [url_finding])

    assert len(results) == 1
    assert results[0].boundary_type == ProductionBoundaryType.EXTERNAL_URL
    assert results[0].externally_reachable is True
    assert results[0].source_environment_id == candidate.id
    assert results[0].source_finding_id == url_finding.id
    assert results[0].source_finding_type == "URLFinding"
    assert results[0].evidence == url_finding.evidence
    assert results[0].metadata["discovery"] == "production_boundary_discovery"
    assert results[0].metadata["source_environment_name"] == "production"


def test_boundary_discovery_produces_external_database_from_production_candidate():
    db_finding = _make_database_finding()
    candidate = _make_environment_candidate(db_finding)

    results = ProductionBoundaryDiscovery().discover([candidate], [db_finding])

    assert len(results) == 1
    assert results[0].boundary_type == ProductionBoundaryType.EXTERNAL_DATABASE
    assert results[0].externally_reachable is True
    assert results[0].source_finding_type == "DatabaseFinding"


def test_boundary_discovery_produces_cloud_resource_from_production_candidate():
    cloud_finding = _make_cloud_finding()
    candidate = _make_environment_candidate(cloud_finding)

    results = ProductionBoundaryDiscovery().discover([candidate], [cloud_finding])

    assert len(results) == 1
    assert results[0].boundary_type == ProductionBoundaryType.CLOUD_RESOURCE
    assert results[0].externally_reachable is True
    assert results[0].source_finding_type == "CloudResourceFinding"


def test_boundary_discovery_excludes_non_production_candidates():
    url_finding = _make_url_finding(environment_hint="staging")
    staging = _make_environment_candidate(
        url_finding, env_name=EnvironmentName.STAGING, candidate_id="env-staging"
    )
    dev_finding = _make_url_finding(
        finding_id="url-dev", hostname="dev.example.com", environment_hint="development"
    )
    development = _make_environment_candidate(
        dev_finding, env_name=EnvironmentName.DEVELOPMENT, candidate_id="env-dev"
    )

    results = ProductionBoundaryDiscovery().discover(
        [staging, development], [url_finding, dev_finding]
    )

    assert results == []


def test_boundary_discovery_marks_localhost_url_as_not_externally_reachable():
    url_finding = _make_url_finding(hostname="localhost")
    candidate = _make_environment_candidate(url_finding)

    results = ProductionBoundaryDiscovery().discover([candidate], [url_finding])

    assert len(results) == 1
    assert results[0].externally_reachable is False


def test_boundary_discovery_marks_internal_hostname_as_not_externally_reachable():
    url_finding = _make_url_finding(hostname="app.internal")
    candidate = _make_environment_candidate(url_finding)

    results = ProductionBoundaryDiscovery().discover([candidate], [url_finding])

    assert len(results) == 1
    assert results[0].externally_reachable is False


def test_boundary_discovery_marks_localhost_database_as_not_externally_reachable():
    db_finding = _make_database_finding(host="127.0.0.1")
    candidate = _make_environment_candidate(db_finding)

    results = ProductionBoundaryDiscovery().discover([candidate], [db_finding])

    assert len(results) == 1
    assert results[0].externally_reachable is False


def test_boundary_discovery_ids_are_deterministic_and_deduplicated():
    url_finding = _make_url_finding()
    candidate = _make_environment_candidate(url_finding)

    first = ProductionBoundaryDiscovery().discover([candidate, candidate], [url_finding])
    second = ProductionBoundaryDiscovery().discover([candidate], [url_finding])

    assert len(first) == 1
    assert first[0].id == second[0].id


def test_boundary_discovery_skips_candidate_with_missing_finding():
    url_finding = _make_url_finding()
    candidate = _make_environment_candidate(url_finding)

    # Pass candidate but no findings — finding lookup should fail gracefully.
    results = ProductionBoundaryDiscovery().discover([candidate], [])

    assert results == []


def test_boundary_confidence_is_derived_from_environment_confidence():
    url_finding = _make_url_finding()
    candidate = _make_environment_candidate(url_finding)
    # candidate.confidence == 0.902, boundary = 0.902 * 0.95 = 0.857

    results = ProductionBoundaryDiscovery().discover([candidate], [url_finding])

    assert results[0].confidence == 0.857


def test_save_boundary_candidates_json_persists_output(tmp_path):
    url_finding = _make_url_finding()
    candidate = _make_environment_candidate(url_finding)
    boundaries = ProductionBoundaryDiscovery().discover([candidate], [url_finding])

    output = save_boundary_candidates_json(
        boundaries, tmp_path / "state" / "boundary_candidates.json"
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert len(payload) == 1
    assert payload[0]["boundary_type"] == "external_url"
    assert payload[0]["externally_reachable"] is True
    assert payload[0]["source_finding_id"] == "url-1"
    assert payload[0]["metadata"]["discovery"] == "production_boundary_discovery"
