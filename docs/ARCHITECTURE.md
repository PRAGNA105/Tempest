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
  -> Production Boundary Discovery
  -> Graph Annotation
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
  -> CLI Artifacts
```

## Module Relationships

- `graph`: language-agnostic `RepositoryGraph`, `Node`, and `Edge` contracts.
- `graphify_adapter`: boundary for converting Graphify output into
  `RepositoryGraph`. The current implementation loads Graphify's
  NetworkX node-link `graphify-out/graph.json` format through
  `GraphifyJsonAdapter`. Optional CLI invocation is isolated in
  `run_graphify_cli` and still hands off through the JSON boundary.
- `scanners`: finding contracts for secrets, URLs, databases, and cloud
  resources.
- `environment`: deterministic environment candidate discovery from scanner
  findings.
- `boundary`: production boundary discovery.
- `annotation`: graph enrichment layer that adds environment and production
  boundary annotation nodes, metadata, and RIM edges.
- `rim`: canonical RIM models and JSON export.
- `detection`: deterministic leak detection contracts and policies that consume
  the RIM.
- `evidence`: deterministic evidence records generated from leak findings and
  RIM nodes.
- `reports`: deterministic report generation from evidence records.
- `rilde_cli`: deterministic command-line orchestration over existing pipeline
  stages.

## Contracts

Every stage exposes explicit inputs and outputs:

| Stage | Input | Output |
| --- | --- | --- |
| Optional Graphify CLI Invocation | Repository path plus command template | `graphify-out/graph.json` |
| Graphify Adapter | Repository path | `RepositoryGraph` |
| Content Scanner | Repository files | Scanner findings |
| Environment Discovery | Scanner findings | Environment candidates |
| Production Boundary Discovery | Environment candidates plus scanner findings | Production boundary candidates |
| Graph Annotation | RIM plus environment and boundary candidates | Annotated RIM |
| RIM Export | Annotated RIM | `rim.json` |
| Leak Detection | Annotated RIM | Leak findings |
| Evidence Generation | RIM plus leak findings | Evidence records |
| Report Generation | Evidence records | Markdown and JSON reports |
| CLI Orchestration | Repository path plus Graphify JSON | Persisted stage artifacts |

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

## Optional Graphify CLI Invocation

`rilde run` can run a user-supplied command before loading Graphify JSON:

```text
--graphify-command <command> [args...]
```

The command is executed without a shell and supports these tokens:

- `{repository}`
- `{graph_json}`
- `{graphify_output_dir}`

The wrapper validates that the expected Graphify JSON exists after the command
completes. It does not change the RILDE graph contract; the JSON adapter remains
the only ingestion boundary.

## Non-Goals For MVP

- No custom AST parser.
- No embeddings.
- No vector database.
- No RAG.
- No MCP.
- No agent layer.
- No remediation.
- No semantic search.
