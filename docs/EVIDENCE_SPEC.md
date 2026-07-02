# Evidence Specification

Evidence generation consumes leak findings and the Repository Intelligence Model
(RIM). It does not parse source files, scanner output, or Graphify output
directly.

## EvidenceRecord

Fields:

- `id`: deterministic evidence identifier.
- `leak_finding_id`: leak finding represented by the record.
- `policy_id`: detection policy that produced the finding.
- `title`: human-readable finding title.
- `severity`: finding severity.
- `summary`: concise evidence summary.
- `source_file`: source file when available.
- `line`: source line when available.
- `column`: source column when available.
- `confidence`: confidence from `0.0` to `1.0`.
- `primary_node`: RIM node snapshot for the primary finding node.
- `related_nodes`: RIM node snapshots for related finding nodes.
- `facts`: deterministic key/value facts derived from finding metadata and RIM
  nodes.
- `metadata`: generator metadata, including missing related node IDs.

## EvidenceNode

Fields:

- `id`: RIM node ID.
- `label`: RIM node label.
- `kind`: RIM node kind.
- `source_file`: source file when available.
- `confidence`: RIM node confidence.
- `metadata`: selected node metadata relevant to evidence.

## EvidenceFact

Fields:

- `key`: fact name.
- `value`: fact value.
- `source_node_id`: RIM node that supports the fact when applicable.

## Current Generator

The deterministic evidence generator creates one evidence record per leak
finding. It snapshots the primary RIM node, snapshots related RIM nodes,
preserves source location and confidence, emits stable facts from leak finding
metadata, and records missing related node IDs without failing generation.
