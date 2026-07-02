from __future__ import annotations

from detection.models import LeakSeverity
from evidence.models import EvidenceRecord
from reports.models import ReportFinding, ReportSummary, SecurityReport

_SEVERITY_ORDER = {
    LeakSeverity.CRITICAL: 0,
    LeakSeverity.HIGH: 1,
    LeakSeverity.MEDIUM: 2,
    LeakSeverity.LOW: 3,
}


def generate_report(records: list[EvidenceRecord]) -> SecurityReport:
    findings = [_report_finding(record) for record in records]
    findings.sort(key=_finding_sort_key)

    return SecurityReport(
        summary=_summary(findings),
        findings=findings,
        metadata={"generator": "deterministic_report_generator"},
    )


def render_markdown_report(report: SecurityReport) -> str:
    lines = [
        f"# {report.title}",
        "",
        "## Summary",
        "",
        f"- Total findings: {report.summary.total_findings}",
        f"- Critical: {report.summary.critical}",
        f"- High: {report.summary.high}",
        f"- Medium: {report.summary.medium}",
        f"- Low: {report.summary.low}",
        "",
        "## Findings",
        "",
    ]

    if not report.findings:
        lines.append("No findings.")
        return "\n".join(lines) + "\n"

    for index, finding in enumerate(report.findings, start=1):
        location = _location(finding)
        lines.extend(
            [
                f"### {index}. {finding.title}",
                "",
                f"- Severity: {finding.severity.value}",
                f"- Policy: {finding.policy_id}",
                f"- Evidence ID: {finding.evidence_id}",
                f"- Location: {location}",
                f"- Confidence: {finding.confidence:.3f}",
                f"- Primary node: {finding.primary_node_id or 'unknown'}",
                f"- Related nodes: {_related_nodes(finding)}",
                f"- Facts: {finding.fact_count}",
                "",
                finding.summary,
                "",
            ]
        )

    return "\n".join(lines)


def _report_finding(record: EvidenceRecord) -> ReportFinding:
    return ReportFinding(
        evidence_id=record.id,
        leak_finding_id=record.leak_finding_id,
        policy_id=record.policy_id,
        title=record.title,
        severity=record.severity,
        source_file=record.source_file,
        line=record.line,
        column=record.column,
        confidence=record.confidence,
        summary=record.summary,
        primary_node_id=record.primary_node.id if record.primary_node else None,
        related_node_ids=[node.id for node in record.related_nodes],
        fact_count=len(record.facts),
    )


def _summary(findings: list[ReportFinding]) -> ReportSummary:
    return ReportSummary(
        total_findings=len(findings),
        critical=sum(1 for finding in findings if finding.severity == LeakSeverity.CRITICAL),
        high=sum(1 for finding in findings if finding.severity == LeakSeverity.HIGH),
        medium=sum(1 for finding in findings if finding.severity == LeakSeverity.MEDIUM),
        low=sum(1 for finding in findings if finding.severity == LeakSeverity.LOW),
    )


def _finding_sort_key(finding: ReportFinding) -> tuple[int, str, str]:
    return (
        _SEVERITY_ORDER[finding.severity],
        finding.source_file or "",
        finding.evidence_id,
    )


def _location(finding: ReportFinding) -> str:
    if finding.source_file is None:
        return "unknown"
    if finding.line is None:
        return finding.source_file
    if finding.column is None:
        return f"{finding.source_file}:{finding.line}"
    return f"{finding.source_file}:{finding.line}:{finding.column}"


def _related_nodes(finding: ReportFinding) -> str:
    if not finding.related_node_ids:
        return "none"
    return ", ".join(finding.related_node_ids)
