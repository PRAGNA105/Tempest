# Current State

## What Exists

- Python 3.12 project configuration.
- Core graph contracts.
- Stub Graphify adapter.
- Graphify JSON adapter for `graphify-out/graph.json`.
- Optional Graphify CLI invocation wrapper.
- Scanner finding contracts.
- Scanner base interface.
- Deterministic source file traversal rules.
- URL scanner.
- Secret scanner.
- Database scanner.
- Cloud resource scanner.
- Environment discovery.
- Production boundary discovery.
- Graph annotation contracts.
- RIM graph annotation for environment and production boundary candidates.
- Leak detection contracts.
- First deterministic leak detection policy.
- Evidence generation contracts.
- Deterministic evidence generation.
- Report generation contracts.
- Deterministic report generation.
- Scanner findings JSON persistence.
- CLI orchestration for the deterministic pipeline.
- RIM node, edge, and model contracts.
- RIM JSON exporter.
- Initial tests.
- Required documentation and state files.

## What Works

- A `RepositoryGraph` can be created from contract models.
- The stub Graphify adapter can return a minimal repository graph.
- The Graphify JSON adapter can load a captured NetworkX node-link fixture.
- The Graphify JSON adapter preserves node/edge metadata and maps confidence
  tags into numeric confidence values.
- The optional Graphify CLI wrapper can run a user-supplied command template
  before the deterministic pipeline reads Graphify JSON.
- `rilde run --graphify-command ...` can invoke Graphify-compatible commands
  with `{repository}`, `{graph_json}`, and `{graphify_output_dir}` tokens.
- Scanner findings can be represented with pydantic models.
- URL findings can be detected from text files with line, column, hostname,
  confidence, and environment hint metadata.
- Secret findings can be detected from text files with redacted evidence,
  entropy, fingerprint metadata, and confidence.
- Database findings can be detected for PostgreSQL, MySQL, MariaDB, MongoDB,
  Redis, SQL Server, JDBC URLs, and database host assignments.
- Cloud resource findings can be detected for AWS, Azure, and GCP resource
  references.
- Environment candidates can be derived from URL, database, and cloud resource
  findings with evidence, confidence, and source finding metadata.
- Production boundary candidates can be derived from production environment
  candidates and scanner findings with externally reachable classification,
  confidence, evidence, and source metadata.
- Scanner findings can be persisted under `state/`.
- Database findings are persisted under `state/database_findings.json`.
- Cloud resource findings are persisted under `state/cloud_findings.json`.
- Environment candidates are persisted under `state/environment_candidates.json`.
- Boundary candidates are persisted under `state/boundary_candidates.json`.
- A RIM can be built from graph nodes, graph edges, and scanner findings.
- A RIM can be annotated with environment and production boundary nodes.
- Environment candidates are linked to source RIM nodes with
  `belongs_to_environment` edges.
- Boundary candidates are linked to source RIM nodes with `crosses_boundary`
  edges.
- Source RIM nodes receive structured annotation metadata.
- Leak findings can be represented with pydantic models.
- Leak findings can be persisted as JSON.
- The production secret boundary policy detects secrets in files that cross
  externally reachable production boundaries.
- Evidence records can be generated from leak findings and RIM nodes.
- Evidence records snapshot primary and related RIM nodes.
- Evidence records include deterministic facts from leak finding metadata.
- Evidence records can be persisted as JSON.
- Structured reports can be generated from evidence records.
- Reports include severity summaries and report-ready finding rows.
- Reports can be rendered as deterministic Markdown.
- Reports can be persisted as JSON and Markdown.
- `rilde run` loads existing Graphify JSON, runs deterministic scanners,
  derives environment and boundary candidates, annotates and exports the RIM,
  runs leak detection, generates evidence, and writes JSON and Markdown report
  artifacts.
- A RIM can be exported as JSON.
- Tests pass with `python -m pytest`: 75 passed.

## What Is Incomplete

- RIM validation CLI.
- Automatic Graphify acquisition when `graph.json` is missing.

## Blockers

- Full-repo `python -m ruff check .` has documented existing lint findings
  outside the latest report files.
- The CLI still expects Graphify output to exist or be produced via an
  explicit `--graphify-command`; there is no built-in auto-discovery or
  default Graphify execution path yet.
