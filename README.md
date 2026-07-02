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

To invoke a Graphify-compatible command first, pass the command last:

```bash
rilde run <repository> --graph-json <repository>/graphify-out/graph.json --output-dir state --graphify-command graphify "{repository}" --output "{graphify_output_dir}"
```

The Graphify command syntax is user-supplied; RILDE only runs it, validates the
expected JSON exists, and then loads that JSON through the adapter boundary.
