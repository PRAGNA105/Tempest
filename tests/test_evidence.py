import json

from annotation import annotate_rim
from boundary import ProductionBoundaryCandidate, ProductionBoundaryType
from detection import LeakSeverity, ProductionSecretBoundaryPolicy
from environment import EnvironmentCandidate, EnvironmentName
from evidence import EvidenceNode, EvidenceRecord, generate_evidence, save_evidence_json
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
        metadata={"scanner": "secret_scanner", "fingerprint": "abc123"},
    )


def _url_finding():
    return URLFinding(
        id="url-1",
        value="https://api.prod.example.com",
        source_file="api.py",
        line=10,
        column=14,
        confidence=0.95,
        evidence="https://api.prod.example.com",
        url="https://api.prod.example.com",
        hostname="api.prod.example.com",
        environment_hint="production",
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


def _boundary_candidate(finding, environment):
    return ProductionBoundaryCandidate(
        id="boundary-1",
        boundary_type=ProductionBoundaryType.EXTERNAL_URL,
        source_environment_id=environment.id,
        source_finding_id=finding.id,
        source_finding_type=finding.__class__.__name__,
        source_file=finding.source_file,
        line=finding.line,
        column=finding.column,
        externally_reachable=True,
        confidence=0.857,
        evidence=finding.evidence or finding.value,
        metadata={"discovery": "production_boundary_discovery"},
    )


def _rim_and_findings():
    secret = _secret_finding()
    url = _url_finding()
    graph = RepositoryGraph(
        nodes=[Node(id="file:api.py", label="api.py", type="file", source_file="api.py")]
    )
    rim = build_rim(graph, [secret, url])
    environment = _environment_candidate(url)
    boundary = _boundary_candidate(url, environment)
    annotated = annotate_rim(rim, [environment], [boundary])
    findings = ProductionSecretBoundaryPolicy().detect(annotated)
    return annotated, findings


def test_evidence_record_contract_accepts_node_and_facts():
    record = EvidenceRecord(
        id="evidence-1",
        leak_finding_id="leak-1",
        policy_id="production_secret_boundary",
        title="Secret in externally reachable production boundary",
        severity=LeakSeverity.CRITICAL,
        summary="summary",
        source_file="api.py",
        line=7,
        column=12,
        confidence=0.857,
        primary_node=EvidenceNode(
            id="finding:secret-1",
            label="api_token",
            kind="secret",
            source_file="api.py",
            confidence=0.95,
        ),
    )

    assert record.primary_node is not None
    assert record.primary_node.kind == "secret"
    assert record.severity == LeakSeverity.CRITICAL


def test_generate_evidence_builds_record_from_rim_and_leak_finding():
    rim, findings = _rim_and_findings()

    records = generate_evidence(rim, findings)

    assert len(records) == 1
    assert records[0].leak_finding_id == findings[0].id
    assert records[0].policy_id == "production_secret_boundary"
    assert records[0].severity == LeakSeverity.CRITICAL
    assert records[0].source_file == "api.py"
    assert records[0].line == 7
    assert records[0].column == 12
    assert records[0].primary_node is not None
    assert records[0].primary_node.id == "finding:secret-1"
    assert records[0].primary_node.metadata["secret_type"] == "api_token"
    assert {node.id for node in records[0].related_nodes} == {
        "file:api.py",
        "boundary:boundary-1",
    }


def test_generate_evidence_includes_deterministic_facts():
    rim, findings = _rim_and_findings()

    records = generate_evidence(rim, findings)
    facts = {(fact.key, fact.value) for fact in records[0].facts}

    assert ("policy_id", "production_secret_boundary") in facts
    assert ("severity", "critical") in facts
    assert ("boundary_type", "external_url") in facts
    assert ("primary_node_kind", "secret") in facts


def test_generate_evidence_ids_are_deterministic_and_missing_nodes_are_recorded():
    rim, findings = _rim_and_findings()
    findings[0].related_node_ids.append("missing:node")

    first = generate_evidence(rim, findings)
    second = generate_evidence(rim, findings)

    assert first[0].id == second[0].id
    assert first[0].metadata["missing_node_ids"] == ["missing:node"]


def test_save_evidence_json_persists_output(tmp_path):
    rim, findings = _rim_and_findings()
    records = generate_evidence(rim, findings)

    output = save_evidence_json(records, tmp_path / "state" / "evidence.json")
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert len(payload) == 1
    assert payload[0]["policy_id"] == "production_secret_boundary"
    assert payload[0]["primary_node"]["kind"] == "secret"
    assert payload[0]["related_nodes"][1]["id"] == "boundary:boundary-1"
