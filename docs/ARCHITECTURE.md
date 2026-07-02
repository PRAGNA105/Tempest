# Architecture

## Architectural Intent

RILDE separates repository understanding from repository reasoning.

Graphify is responsible for extracting repository facts. RILDE is responsible
for turning those facts plus deterministic scanner findings into a
security-aware Repository Intelligence Model (RIM). Leak detection consumes the
RIM later; it does not parse source code directly.

## MVP Data Flow

```text
Repository
  -> Graphify Adapter
  -> Repository Graph
  -> Content Scanner
  -> Environment Discovery
  -> RIM Export
```

## Target Data Flow

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
```

## Module Relationships

- `graph`: language-agnostic `RepositoryGraph`, `Node`, and `Edge` contracts.
- `graphify_adapter`: boundary for converting Graphify output into
  `RepositoryGraph`. The current implementation loads Graphify's
  NetworkX node-link `graphify-out/graph.json` format through
  `GraphifyJsonAdapter`.
- `scanners`: finding contracts for secrets, URLs, databases, and cloud
  resources.
- `environment`: deterministic environment candidate discovery from scanner
  findings.
- `boundary`: future production boundary discovery.
- `annotation`: future graph enrichment layer.
- `rim`: canonical RIM models and JSON export.
- `detection`: future leak detection engine.
- `evidence`: future evidence generation.
- `reports`: future report generation.

## Contracts

Every stage exposes explicit inputs and outputs:

| Stage | Input | Output |
| --- | --- | --- |
| Graphify Adapter | Repository path | `RepositoryGraph` |
| Content Scanner | Repository files | Scanner findings |
| Environment Discovery | Scanner findings | Environment candidates |
| RIM Export | `RepositoryGraph` plus findings | `rim.json` |
| Leak Detection | RIM | Findings and evidence |

## Graphify JSON Boundary

RILDE reads Graphify output from:

```text
graphify-out/graph.json
```

The adapter supports the NetworkX node-link shape used by Graphify:

- `nodes`: graph nodes.
- `links`: graph edges.
- `edges`: accepted as a compatibility alias for `links`.
- `graph`: graph-level metadata preserved in `RepositoryGraph.metadata`.

Graphify node metadata is preserved under `Node.metadata`. Graphify edge
confidence tags are converted to numeric confidence:

- `EXTRACTED`: `1.0`
- `INFERRED`: `confidence_score` when present, otherwise `0.75`
- `AMBIGUOUS`: `0.5`

## Non-Goals For MVP

- No custom AST parser.
- No embeddings.
- No vector database.
- No RAG.
- No MCP.
- No agent layer.
- No remediation.
- No semantic search.
