# Detection Specification

Leak detection consumes the Repository Intelligence Model (RIM). It does not
parse source files or Graphify output directly.

## Contracts

### LeakFinding

Fields:

- `id`: deterministic finding identifier.
- `policy_id`: policy that produced the finding.
- `title`: human-readable finding title.
- `severity`: `low`, `medium`, `high`, or `critical`.
- `source_node_id`: primary RIM node responsible for the finding.
- `source_file`: source file when available.
- `line`: source line when available.
- `column`: source column when available.
- `confidence`: confidence from `0.0` to `1.0`.
- `evidence`: concise evidence summary.
- `related_node_ids`: other RIM nodes involved in the finding.
- `metadata`: policy-specific structured context.

### DetectionResult

Fields:

- `policy_id`: policy that produced the result.
- `findings`: leak findings from the policy.
- `metadata`: execution metadata.

## Current Policies

### production_secret_boundary

Detects secrets in files that also cross externally reachable production
boundaries.

Inputs:

- Annotated RIM secret nodes.
- `crosses_boundary` edges.
- Production boundary nodes with candidate metadata where
  `externally_reachable` is `true`.

Output:

- One deterministic `LeakFinding` per secret and externally reachable production
  boundary in the same source file.
