import json

from annotation import annotate_rim
from boundary import ProductionBoundaryCandidate, ProductionBoundaryType
from detection import (
    LeakFinding,
    LeakSeverity,
    ProductionSecretBoundaryPolicy,
    save_leak_findings_json,
)
from environment import EnvironmentCandidate, EnvironmentName
from graph import Node, RepositoryGraph
from rim import build_rim
from scanners import SecretFinding, URLFinding


def _secret_finding():
    return SecretFinding(
        id="secret-1",
        value="redacted",
        source_file="api.py",
        line=7,
        column=12,
        confidence=0.95,
        evidence="API_TOKEN=redacted",
        secret_type="api_token",
        entropy=4.5,
        metadata={"scanner": "secret_scanner"},
    )


def _url_finding(hostname="api.prod.example.com", environment_hint="production"):
    return URLFinding(
        id="url-1",
        value=f"https://{hostname}",
        source_file="api.py",
        line=10,
        column=14,
        confidence=0.95,
        evidence=f"https://{hostname}",
        url=f"https://{hostname}",
        hostname=hostname,
        environment_hint=environment_hint,
        metadata={"scanner": "url_scanner"},
    )


def _environment_candidate(finding):
    return EnvironmentCandidate(
        id="environment-1",
        name=EnvironmentName.PRODUCTION,
        source_finding_id=finding.id,
        source_finding_type=finding.__class__.__name__,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        confidence=0.902,
        evidence=finding.evidence or finding.value,
        metadata={"discovery": "environment_discovery"},
    )


def _boundary_candidate(finding, environment, *, externally_reachable=True):
    return ProductionBoundaryCandidate(
        id="boundary-1",
        boundary_type=ProductionBoundaryType.EXTERNAL_URL,
        source_environment_id=environment.id,
        source_finding_id=finding.id,
        source_finding_type=finding.__class__.__name__,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        externally_reachable=externally_reachable,
        confidence=0.857,
        evidence=finding.evidence or finding.value,
        metadata={"discovery": "production_boundary_discovery"},
    )


def _annotated_rim(*, externally_reachable=True):
    secret = _secret_finding()
    url = _url_finding()
    graph = RepositoryGraph(
        nodes=[Node(id="file:api.py", label="api.py", type="file", source_file="api.py")]
    )
    rim = build_rim(graph, [secret, url])
    environment = _environment_candidate(url)
    boundary = _boundary_candidate(
        url,
        environment,
        externally_reachable=externally_reachable,
    )
    return annotate_rim(rim, [environment], [boundary])


def test_leak_finding_contract_accepts_policy_output_shape():
    finding = LeakFinding(
        id="leak-1",
        policy_id="production_secret_boundary",
        title="Secret in externally reachable production boundary",
        severity=LeakSeverity.HIGH,
        source_node_id="finding:secret-1",
        source_file="api.py",
        line=7,
        column=12,
        confidence=0.85,
        evidence="secret evidence",
        related_node_ids=["file:api.py", "boundary:boundary-1"],
    )

    assert finding.severity == LeakSeverity.HIGH
    assert finding.related_node_ids == ["file:api.py", "boundary:boundary-1"]


def test_production_secret_boundary_policy_detects_secret_in_external_boundary_file():
    rim = _annotated_rim()

    findings = ProductionSecretBoundaryPolicy().detect(rim)

    assert len(findings) == 1
    assert findings[0].policy_id == "production_secret_boundary"
    assert findings[0].severity == LeakSeverity.CRITICAL
    assert findings[0].source_node_id == "finding:secret-1"
    assert findings[0].source_file == "api.py"
    assert findings[0].line == 7
    assert findings[0].column == 12
    assert findings[0].confidence == 0.857
    assert findings[0].metadata["boundary_type"] == "external_url"
    assert findings[0].metadata["boundary_source_node_id"] == "file:api.py"
    assert "api_token" in findings[0].evidence


def test_production_secret_boundary_policy_skips_internal_boundary():
    rim = _annotated_rim(externally_reachable=False)

    findings = ProductionSecretBoundaryPolicy().detect(rim)

    assert findings == []


def test_production_secret_boundary_policy_ids_are_deterministic_and_deduplicated():
    rim = _annotated_rim()
    policy = ProductionSecretBoundaryPolicy()

    first = policy.detect(rim)
    second = policy.detect(rim)

    assert len(first) == 1
    assert first[0].id == second[0].id


def test_save_leak_findings_json_persists_output(tmp_path):
    rim = _annotated_rim()
    findings = ProductionSecretBoundaryPolicy().detect(rim)

    output = save_leak_findings_json(findings, tmp_path / "state" / "leak_findings.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert len(payload) == 1
    assert payload[0]["policy_id"] == "production_secret_boundary"
    assert payload[0]["severity"] == "critical"
    assert payload[0]["metadata"]["externally_reachable"] is True
