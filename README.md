# Repository Intelligence and Leak Detection Engine

RILDE builds a security-aware Repository Intelligence Model (RIM) from a
Graphify-derived repository graph and deterministic scanner findings.

The current MVP is intentionally narrow:

1. Load an existing Graphify repository graph.
2. Normalize it behind stable graph contracts.
3. Run deterministic scanners and discovery stages.
4. Export an annotated JSON RIM.
5. Generate leak findings, evidence records, and JSON/Markdown reports.

Run the deterministic pipeline with:

```bash
rilde run <repository> --graph-json <repository>/graphify-out/graph.json --output-dir state
```

Graphify CLI invocation is still optional future work; the current pipeline
expects Graphify JSON to already exist.
