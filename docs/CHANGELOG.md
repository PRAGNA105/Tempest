# Changelog

## 2026-07-02 (Session 7)

### Added

- Added `rilde` console script entry point.
- Added `rilde run` deterministic pipeline orchestration.
- Added reusable CLI pipeline orchestration that loads Graphify JSON, runs
  scanners, derives environment and boundary candidates, annotates and exports
  the RIM, runs leak detection, generates evidence, and writes report artifacts.
- Added CLI orchestration tests (3 new tests).

## 2026-07-02 (Session 6)

### Added

- Added report contracts for summaries, report findings, and security reports.
- Added deterministic report generation from evidence records.
- Added Markdown report rendering.
- Added report JSON and Markdown persistence.
- Added report specification documentation.
- Added report generation tests (5 new tests).

## 2026-07-02 (Session 5)

### Added

- Added evidence generation contracts for evidence records, evidence nodes, and
  evidence facts.
- Added deterministic evidence generation from leak findings and RIM nodes.
- Added evidence JSON persistence.
- Added evidence specification documentation.
- Added evidence generation tests (5 new tests).

## 2026-07-02 (Session 4)

### Added

- Added leak detection contracts for severity, leak findings, and detection
  results.
- Added detection policy interface.
- Added production secret boundary policy for secrets colocated with externally
  reachable production boundaries in annotated RIM data.
- Added leak finding JSON persistence.
- Added detection specification documentation.
- Added leak detection tests (5 new tests).

## 2026-07-02 (Session 3)

### Added

- Added graph annotation contracts for annotation type and annotated node
  metadata.
- Added RIM annotation that creates environment and production boundary nodes.
- Added `belongs_to_environment` and `crosses_boundary` RIM edges from source
  nodes to annotation nodes.
- Added source node annotation metadata enrichment with file-node resolution and
  finding-node fallback.
- Added graph annotation tests (5 new tests).
- Added the missing `docs/HANDOFF.md` handoff source.

## 2026-07-02 (Session 2)

### Added

- Added production boundary discovery contracts and discovery logic.
- Added production boundary candidate derivation from production environment
  candidates with externally reachable classification.
- Added boundary candidate JSON persistence.
- Added production boundary discovery tests (11 new tests).

## 2026-07-02


### Added

- Added deterministic environment discovery contracts.
- Added environment candidate derivation from URL, database, and cloud resource
  findings.
- Added environment candidate JSON persistence and discovery script.
- Added environment discovery tests.

## 2026-07-01

### Added

- Bootstrapped repository structure.
- Added graph contracts.
- Added Graphify adapter boundary and stub adapter.
- Added scanner finding contracts.
- Added RIM contracts and JSON exporter.
- Added initial tests.
- Added mandatory documentation and state tracking files.
- Verified tests with `python -m pytest`.

### Changed

- Added `GraphifyJsonAdapter` for Graphify's `graphify-out/graph.json`
  NetworkX node-link output.
- Added a captured Graphify-style fixture and adapter tests.
- Added scanner base interface, source traversal rules, URL scanner, findings
  persistence, and URL scanner tests.
- Added deterministic secret scanner with common patterns, entropy scoring,
  redacted persistence, and tests.
- Added deterministic database scanner for PostgreSQL, MySQL, MariaDB,
  MongoDB, Redis, SQL Server, JDBC URLs, and host assignments.
- Added deterministic cloud resource scanner for AWS, Azure, and GCP resource
  references.
- Added database and cloud scanner persistence scripts and tests.
- Extended traversal to Terraform `.tf` and `.tfvars` files.
