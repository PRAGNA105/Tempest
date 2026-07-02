# Project Handoff

## Project

RILDE - Repository Intelligence and Leak Detection Engine.

## Current Milestone

CLI.

## Last Completed Task

Optional Graphify CLI invocation wrapper.

## Current Task

No active task.

## Next Task

RIM validation CLI.

## Blockers

- Full-repo `python -m ruff check .` has documented existing lint findings
  outside the latest report files.

## Test Status

Pass. `python -m pytest`: 75 passed.

## Architecture Snapshot

RILDE converts repository facts and deterministic scanner findings into a
security-aware Repository Intelligence Model (RIM).

Major modules:

- `graph`: language-agnostic repository graph contracts.
- `graphify_adapter`: loads Graphify NetworkX node-link JSON into graph
  contracts and can optionally invoke a user-supplied Graphify CLI command
  before JSON loading.
- `scanners`: URL, secret, database, and cloud resource finding contracts and
  deterministic scanners.
- `environment`: derives environment candidates from scanner findings.
- `boundary`: derives production boundary candidates from production
  environment candidates.
- `annotation`: enriches the RIM with environment and production boundary
  annotation nodes, metadata, and edges.
- `rim`: canonical model and JSON export.
- `detection`: deterministic leak detection contracts and policies.
- `evidence`: deterministic evidence records generated from leak findings and
  RIM nodes.
- `reports`: deterministic structured, Markdown, and JSON report generation
  from evidence records.
- `rilde_cli`: deterministic CLI orchestration and console entry point.

Data flow:

```text
Repository
  -> Graphify Adapter
  -> Repository Graph
  -> Content Scanner
  -> Environment Discovery
  -> Production Boundary Discovery
  -> Graph Annotation
  -> Repository Intelligence Model
  -> Leak Detection Engine
  -> Evidence Generation
  -> Reports
  -> CLI Artifacts
```

Contracts:

- Graphify output is normalized to `RepositoryGraph`.
- Optional Graphify CLI invocation produces Graphify JSON before the adapter
  boundary; it does not alter the RIM contract.
- Scanner output is represented as typed `Finding` models.
- Environment and boundary discovery output candidate models.
- Annotation consumes a RIM plus candidates and returns an enriched RIM.
- Leak detection consumes the annotated RIM and returns leak findings.
- Evidence generation consumes leak findings plus the RIM and returns evidence
  records.
- Report generation consumes evidence records and returns report outputs.
- CLI orchestration composes the deterministic stages and persists artifacts.

## Important Decisions

- Graphify is the source of repository understanding.
- RIM is the central contract between repository intelligence and leak
  detection.
- Detection operates on RIM, not raw source code.
- MVP remains deterministic and avoids AI infrastructure.
- JSON persistence comes before database persistence.

## Current Risks

- Python target is 3.12+, but local test output currently shows Python 3.10.11.
- Full-repo Ruff has existing findings outside the latest report work.
- RIM validation CLI is not implemented.

## Immediate Next Action

The next engineer should start by executing:

```text
RIM validation CLI.
```
