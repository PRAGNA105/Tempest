import json

from detection import LeakSeverity
from evidence import EvidenceFact, EvidenceNode, EvidenceRecord
from reports import (
    ReportFinding,
    SecurityReport,
    generate_report,
    render_markdown_report,
    save_report_json,
    save_report_markdown,
)


def _record(
    evidence_id: str = "evidence-1",
    severity: LeakSeverity = LeakSeverity.CRITICAL,
    source_file: str = "api.py",
):
    return EvidenceRecord(
        id=evidence_id,
        leak_finding_id=f"leak-{evidence_id}",
        policy_id="production_secret_boundary",
        title="Secret in externally reachable production boundary",
        severity=severity,
        summary=f"{severity.value} finding in {source_file}",
        source_file=source_file,
        line=7,
        column=12,
        confidence=0.857,
        primary_node=EvidenceNode(
            id=f"finding:{evidence_id}",
            label="api_token",
            kind="secret",
            source_file=source_file,
            confidence=0.95,
        ),
        related_nodes=[
            EvidenceNode(
                id=f"boundary:{evidence_id}",
                label="external_url",
                kind="production_boundary",
                source_file=source_file,
                confidence=0.857,
            )
        ],
        facts=[
            EvidenceFact(key="severity", value=severity.value),
            EvidenceFact(key="boundary_type", value="external_url"),
        ],
    )


def test_report_contract_accepts_findings_and_summary():
    report = SecurityReport(
        findings=[
            ReportFinding(
                evidence_id="evidence-1",
                leak_finding_id="leak-1",
                policy_id="production_secret_boundary",
                title="Secret in externally reachable production boundary",
                severity=LeakSeverity.CRITICAL,
                source_file="api.py",
                line=7,
                column=12,
                confidence=0.857,
                summary="summary",
                primary_node_id="finding:secret-1",
                related_node_ids=["boundary:boundary-1"],
                fact_count=2,
            )
        ]
    )

    assert report.schema_version == "0.1"
    assert report.findings[0].severity == LeakSeverity.CRITICAL


def test_generate_report_summarizes_and_sorts_findings_by_severity():
    records = [
        _record("evidence-low", LeakSeverity.LOW, "low.py"),
        _record("evidence-critical", LeakSeverity.CRITICAL, "critical.py"),
        _record("evidence-high", LeakSeverity.HIGH, "high.py"),
    ]

    report = generate_report(records)

    assert report.summary.total_findings == 3
    assert report.summary.critical == 1
    assert report.summary.high == 1
    assert report.summary.low == 1
    assert [finding.severity for finding in report.findings] == [
        LeakSeverity.CRITICAL,
        LeakSeverity.HIGH,
        LeakSeverity.LOW,
    ]
    assert report.findings[0].source_file == "critical.py"


def test_render_markdown_report_includes_summary_and_finding_details():
    report = generate_report([_record()])

    markdown = render_markdown_report(report)

    assert "# RILDE Security Report" in markdown
    assert "- Total findings: 1" in markdown
    assert "- Severity: critical" in markdown
    assert "- Location: api.py:7:12" in markdown
    assert "critical finding in api.py" in markdown


def test_render_markdown_report_handles_empty_report():
    report = generate_report([])

    markdown = render_markdown_report(report)

    assert "- Total findings: 0" in markdown
    assert "No findings." in markdown


def test_report_persistence_writes_json_and_markdown(tmp_path):
    report = generate_report([_record()])

    json_output = save_report_json(report, tmp_path / "reports" / "report.json")
    markdown_output = save_report_markdown(report, tmp_path / "reports" / "report.md")
    payload = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = markdown_output.read_text(encoding="utf-8")

    assert payload["summary"]["total_findings"] == 1
    assert payload["findings"][0]["severity"] == "critical"
    assert markdown.startswith("# RILDE Security Report")
