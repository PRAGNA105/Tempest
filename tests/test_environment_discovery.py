import json

from environment import (
    EnvironmentDiscovery,
    EnvironmentName,
    save_environment_candidates_json,
)
from scanners import (
    CloudProvider,
    CloudResourceFinding,
    DatabaseFinding,
    SecretFinding,
    URLFinding,
)


def test_environment_discovery_uses_url_and_database_environment_hints():
    findings = [
        URLFinding(
            id="url-1",
            value="https://api.prod.example.com",
            source_file="settings.py",
            line=1,
            column=10,
            confidence=0.95,
            evidence="https://api.prod.example.com",
            url="https://api.prod.example.com",
            hostname="api.prod.example.com",
            environment_hint="production",
            metadata={"scanner": "url_scanner"},
        ),
        DatabaseFinding(
            id="database-1",
            value="postgresql://staging-db.example.com/app",
            source_file="settings.py",
            line=2,
            column=14,
            confidence=0.9,
            evidence="postgresql://staging-db.example.com/app",
            database_type="postgresql",
            host="staging-db.example.com",
            database_name="app",
            environment_hint="staging",
            metadata={"scanner": "database_scanner"},
        ),
    ]

    candidates = EnvironmentDiscovery().discover(findings)

    assert [candidate.name for candidate in candidates] == [
        EnvironmentName.PRODUCTION,
        EnvironmentName.STAGING,
    ]
    assert candidates[0].source_finding_id == "url-1"
    assert candidates[0].source_finding_type == "URLFinding"
    assert candidates[0].confidence == 0.902
    assert candidates[0].metadata["signal"] == "explicit_hint"
    assert candidates[1].evidence == "postgresql://staging-db.example.com/app"


def test_environment_discovery_infers_cloud_resource_environment_from_tokens():
    findings = [
        CloudResourceFinding(
            id="cloud-1",
            value="arn:aws:lambda:us-east-1:123456789012:function:prod-worker",
            source_file="infra.tf",
            line=4,
            column=20,
            confidence=0.95,
            evidence="arn:aws:lambda:us-east-1:123456789012:function:prod-worker",
            provider=CloudProvider.AWS,
            resource_type="lambda_function",
            resource_id="prod-worker",
            region="us-east-1",
            metadata={"scanner": "cloud_resource_scanner"},
        ),
        CloudResourceFinding(
            id="cloud-2",
            value="gs://qa-assets",
            source_file="infra.tf",
            line=5,
            column=10,
            confidence=0.92,
            evidence="gs://qa-assets",
            provider=CloudProvider.GCP,
            resource_type="gcs_bucket",
            resource_id="qa-assets",
            metadata={"scanner": "cloud_resource_scanner"},
        ),
    ]

    candidates = EnvironmentDiscovery().discover(findings)

    assert [candidate.name for candidate in candidates] == [
        EnvironmentName.PRODUCTION,
        EnvironmentName.QA,
    ]
    assert candidates[0].confidence == 0.76
    assert candidates[0].metadata["signal"] == "resource_token"
    assert candidates[0].metadata["source_scanner"] == "cloud_resource_scanner"


def test_environment_discovery_ignores_findings_without_environment_signals():
    findings = [
        SecretFinding(
            id="secret-1",
            value="AKIA...MPLE",
            source_file="settings.env",
            secret_type="aws_access_key_id",
            confidence=0.95,
        ),
        CloudResourceFinding(
            id="cloud-1",
            value="arn:aws:sns:us-east-1:123456789012:alerts",
            source_file="infra.tf",
            confidence=0.95,
            provider=CloudProvider.AWS,
            resource_type="sns_resource",
            resource_id="alerts",
        ),
    ]

    assert EnvironmentDiscovery().discover(findings) == []


def test_environment_candidate_ids_are_deterministic_and_deduplicated():
    finding = URLFinding(
        id="url-1",
        value="https://dev.example.com",
        source_file="settings.py",
        url="https://dev.example.com",
        hostname="dev.example.com",
        environment_hint="development",
    )

    first = EnvironmentDiscovery().discover([finding, finding])
    second = EnvironmentDiscovery().discover([finding])

    assert len(first) == 1
    assert first[0].id == second[0].id


def test_save_environment_candidates_json_persists_output(tmp_path):
    finding = URLFinding(
        id="url-1",
        value="https://api.prod.example.com",
        source_file="settings.py",
        url="https://api.prod.example.com",
        hostname="api.prod.example.com",
        environment_hint="production",
    )
    candidates = EnvironmentDiscovery().discover([finding])

    output = save_environment_candidates_json(
        candidates, tmp_path / "state" / "environment_candidates.json"
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload[0]["name"] == "production"
    assert payload[0]["source_finding_id"] == "url-1"
    assert payload[0]["metadata"]["discovery"] == "environment_discovery"
