# Repository Intelligence and Leak Detection Engine

RILDE builds a security-aware Repository Intelligence Model (RIM) from a
Graphify-derived repository graph and deterministic scanner findings.

The current MVP is intentionally narrow:

1. Load or receive a repository graph.
2. Normalize it behind stable graph contracts.
3. Represent scanner findings as explicit contracts.
4. Export a JSON RIM for downstream leak detection.

Future phases can add leak detection, evidence reports, incremental indexing,
and AI-facing features, but those are not dependencies of the MVP.

