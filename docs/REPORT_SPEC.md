# Report Specification

Report generation consumes evidence records. It does not parse source files,
scanner output, Graphify output, RIM data, or leak findings directly.

## SecurityReport

Fields:

- `schema_version`: report schema version.
- `title`: human-readable report title.
- `summary`: aggregate finding counts.
- `findings`: report-ready finding rows.
- `metadata`: generator metadata.

## ReportSummary

Fields:

- `total_findings`
- `critical`
- `high`
- `medium`
- `low`

## ReportFinding

Fields:

- `evidence_id`: evidence record represented by the row.
- `leak_finding_id`: leak finding represented by the evidence.
- `policy_id`: detection policy that produced the leak finding.
- `title`: finding title.
- `severity`: `low`, `medium`, `high`, or `critical`.
- `source_file`: source file when available.
- `line`: source line when available.
- `column`: source column when available.
- `confidence`: confidence from `0.0` to `1.0`.
- `summary`: concise evidence summary.
- `primary_node_id`: primary RIM node ID when available.
- `related_node_ids`: related RIM node IDs.
- `fact_count`: number of deterministic evidence facts.

## Current Outputs

The report generator produces:

- Structured `SecurityReport` data.
- Deterministic Markdown output.
- JSON persistence.
- Markdown persistence.

Findings are sorted by severity, then source file, then evidence ID.
