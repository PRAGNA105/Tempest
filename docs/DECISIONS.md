# Decisions

Decision:
Use Graphify as the repository understanding layer.

Reason:
Graphify already handles parsing, language support, symbols, and base graph
construction. RILDE should build security intelligence on top.

Alternatives:
Build a custom AST parser, use Tree-sitter directly, or implement a custom
knowledge graph builder.

Date:
2026-07-01

---

Decision:
Keep the MVP deterministic and avoid AI infrastructure.

Reason:
The immediate goal is a reliable repository graph to RIM export pipeline.
Embeddings, vector search, RAG, MCP, and agents add complexity before the core
security model is proven.

Alternatives:
Introduce embeddings and semantic search in the first version.

Date:
2026-07-01

---

Decision:
Make RIM the central contract between repository intelligence and leak
detection.

Reason:
Leak detection should consume a stable security-aware model, not parser-specific
or Graphify-specific data.

Alternatives:
Let leak detection read Graphify output directly.

Date:
2026-07-01

