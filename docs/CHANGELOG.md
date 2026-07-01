# Changelog

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
