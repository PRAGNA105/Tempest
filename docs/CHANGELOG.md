# Changelog

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
