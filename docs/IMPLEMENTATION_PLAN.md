# Implementation Plan

## Current Sprint

Complete deterministic repository intelligence foundations:

- URL scanner complete.
- Secret scanner complete.
- Database scanner complete.
- Cloud resource scanner complete.
- Environment discovery complete.
- Production boundary discovery complete.
- Graph annotation complete.
- Leak detection policies complete.
- Evidence generation complete.
- Report generation complete.
- Scanner findings persistence complete.
- CLI orchestration complete.
- Optional Graphify CLI invocation wrapper complete.
- Tests and documentation updated.
- Automatic Graphify acquisition when `graph.json` is absent.

Plan for automatic Graphify support:

1. Define the default Graphify acquisition behavior for `rilde run` when no
   `--graph-json` is supplied.
2. Add a discovery and execution path that can invoke Graphify with sensible
   defaults, generate `graphify-out/graph.json`, and reuse the existing JSON
   adapter boundary.
3. Keep the explicit `--graphify-command` escape hatch for custom workflows
   and CI environments.
4. Update the CLI help, README, and docs so users can run the project without
   pre-creating `graph.json`.
5. Add tests for the automatic path, missing Graphify installation, and
   fallback/error messages.

## MVP Roadmap

1. Repository graph interface.
2. Graphify adapter stub.
3. Scanner contracts.
4. RIM contracts.
5. RIM JSON export.
6. Deterministic scanners. URL, secret, database, and cloud scanner
   foundations are complete.
7. Environment discovery.
8. Production boundary discovery. Complete.
9. Graph annotation. Complete.
10. Leak detection policies. Complete.
11. Evidence generation. Complete.
12. Reports. Complete.
13. CLI. Complete.
14. Automatic Graphify acquisition.

## Future Sprints

- JSON state persistence for every stage.
- RIM validation CLI.
- Leak detection traversal and policies.
- Graphify auto-discovery and default execution hardening.

## Backlog

- Incremental repository updates.
- Performance profiling.
- More policy types.
- MCP integration.
- Semantic search.
- Embeddings and vector indexes.
- Repository assistant workflows.
