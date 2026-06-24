# Unified Leak Detection Agent: System Architecture Document

This document defines the production architecture for the **Unified Leak Detection Agent**, an air-gapped, locally executed security defense engine. 

Unlike traditional static application security testing (SAST) tools that rely solely on regular expressions, this architecture introduces a **Specialized Agentic System**. It decouples declarative security reasoning (**Skills**) from deterministic programmatic execution (**Tools**), unifying Abstract Syntax Tree (AST) reachability math, payload density inspection, and operating system environmental profiling into a single developer-friendly checkpoint.

---

## 1. Executive Summary & Core Principles

The primary objective of this system is to prevent cross-environment data contamination (e.g., routing test data to production sinks or staging non-production secrets) and environmental credential leakage *before* code leaves the developer's physical machine.

### Architectural Guardrails
* **100% Local Execution:** All parsing, graph traversals, and evaluations happen locally on the developer's CPU. Zero source code, file diffs, or execution graphs are ever transmitted over a network.
* **Air-Gapped AI Supervision:** When integrated with AI coding assistants (e.g., Claude Code, GitHub Copilot), the agent acts strictly as a local diagnostic data provider. It does not make external API calls.
* **Cognitive Decoupling:** Business logic and threat definitions are maintained as declarative prompt instructions (`.md`), while hard CPU-intensive operations (AST parsing, regex matching) are maintained as compiled Python tools.
* **Zero Developer Friction:** The entire verification pipeline executes in under 3 seconds during standard developer habits (`git commit` or IDE diagnostics).

---

## 2. Threat Model & Problem Catalogue Mapping

The architecture is structured to solve 18 distinct failure modes observed in enterprise development. The system categorizes threats into three defense tiers.

### Tier 1: Semantic Trace Leaks (The Graph Engine)
Threats representing control-flow bridges or data-flow contamination that can only be detected by understanding code execution intent.
* **P-10 (Prod-named variables masking placeholders):** AST variable taxonomy vs environment boundaries.
* **P-11 (Prod URL in non-prod config):** Pathfinding blocks non-prod entry nodes reaching prod configs.
* **P-12 (Multi-hop import chains):** Depth-First Search (DFS) traces multi-file import chains.
* **P-13 (Dynamic string construction):** Static Taint Analysis traces dynamic variable flow.
* **P-14 (Aliased production identifiers):** Tracks dictionary alias references to runtime endpoints.

### Tier 2: Content-Based Leaks (The Payload Engine)
Threats representing physical files containing unauthorized credentials or raw customer data. Intercepted via Git file diffs and routed to pattern scanners.
* **P-01 (Hardcoded credentials) & P-02 (Secrets in un-ignored `.env` files):** Evaluated against cryptographic regex suites.
* **P-04 (Customer data in fixtures) & P-07 (VCR Cassettes):** Routed to Named Entity Recognition (NER) models for PII density.
* **P-05 (PII embedded in Jupyter notebooks):** Pre-processor strips `.ipynb` JSON wrappers to inspect raw outputs.
* **P-06 (Secrets inside build artifacts) & P-08 (IDE artifacts):** Staging hooks block binary extensions while running strict regex.

### Tier 3: Out-of-Band & Runtime Leaks (The Environment Engine)
Threats existing completely outside the repository boundary or purely in active terminal memory.
* **P-03 (Tooling configs) & P-18 (Dotfile repos):** Agent reads absolute OS paths (`~/.aws/credentials`, `~/.kube/config`).
* **P-16 (Production IPs in `/etc/hosts`):** Agent reads the local system network routing table.
* **P-15 (Active kubeconfig context):** Shell wrapper executes `kubectl config current-context` to verify cluster state.
* **P-09 (Secrets in shell history):** Shell interceptors parse memory buffers (`~/.zsh_history`).

---

## 3. The Agentic Abstraction Model

To ensure the architecture remains maintainable and extensible, the system strictly separates the "Brain" from the "Hands." 

    +-------------------------------------------------------------------------+
    |                        DECLARATIVE SKILL LAYER                          |
    |             (.agent/skills/*.md — Prompt-as-Code Rulesets)              |
    +------------------------------------+------------------------------------+
                                         │
                                         │ 1. Evaluates Intent & Selects Tools
                                         ▼
    +-------------------------------------------------------------------------+
    |                          PYTHON ORCHESTRATOR                            |
    |                 (orchestrator.py — The Execution Brain)                 |
    +------------------------------------+------------------------------------+
                                         │
                                         │ 2. Delegates Raw Byte Operations
                                         ▼
    +-------------------------------------------------------------------------+
    |                         DUMB TOOL REGISTRY                              |
    |           (tools/*.py — Pure Deterministic Execution Scripts)           |
    +-------------------------------------------------------------------------+

---

## 4. Universal Interface Layer (The AI Adapters)

To ensure zero vendor lock-in, the system exposes its internal detection engines through three lightweight communication adapters.

| Adapter Type | Core Technology | Primary Consumers | Operational Mechanism |
|---|---|---|---|
| **MCP Adapter** | JSON-RPC over `stdio` | Claude Code, Cursor | Exposes engines as discrete, autonomous tools for LLMs. |
| **LSP Adapter** | Python `pygls` Framework | GitHub Copilot, VS Code | Broadcasts graph diagnostics as editor squiggly lines. |
| **CLI Adapter** | Standard I/O streams | Git Hooks, CI/CD | Executes blocking zero-or-one terminal exit codes. |

---

## 5. Directory & Package Hierarchy

### Local Project Sector (The Sandbox)
    my-enterprise-app/
    ├── .git/hooks/pre-commit           # Bash routing script intercepting staged diffs
    ├── .agent/skills/                  # Declarative instruction prompt files
    ├── graphify-out/graph.json         # Local AST topological map (Git-ignored)
    └── src/                            # Application source code

### Python Distribution Package (The Global Engine)
    leak_detector_agent/
    ├── cli.py                          # Terminal entrypoint 
    ├── orchestrator.py                 # Skill parser and delegator
    ├── adapters/                       # Universal Interface Layer (MCP, LSP, CLI)
    ├── engines/                        # Specialized Execution Logic
    │   ├── graph_engine.py             
    │   ├── payload_engine.py           
    │   └── environment_engine.py       
    └── tools/                          # Dumb registry tools (AST, I/O, OS path reading)

---

## 6. Complete System Topology

    ===================================================================================================
                                      DEVELOPER MACHINE LOCAL BOUNDARY
                                   (Air-Gapped: Zero Outbound Network Calls)
    ===================================================================================================

      [1. CLIENT INTERFACES]
         +---------------+    +---------------+    +---------------+    +---------------+
         |  Claude Code  |    | Cursor / Zed  |    | GitHub Copilot|    |  Git Hook     |
         +-------+-------+    +-------+-------+    +-------+-------+    +-------+-------+
                 │                    │                    │                    │
                 └─────────┬──────────┘                    │                    │
                           │ JSON-RPC / stdio              │ LSP Diagnostics    │ Process Exit (0/1)
                           ▼                               ▼                    ▼
      [2. UNIVERSAL INTERFACE LAYER]
         +-----------------------------------+ +-----------------------+ +----------------------+
         |          MCP ADAPTER              | |      LSP ADAPTER      | |     CLI ADAPTER      |
         +----------------─┬-----------------+ +-----------┬-----------+ +----------┬-----------+
                           │                               │                        │
                           └───────────────┬───────────────┴────────────────────────┘
                                           ▼
      [3. COGNITIVE ORCHESTRATION]
         +==================================================================================+
         |                       CENTRAL AGENT ORCHESTRATOR                                 |
         +=========================================┬========================================+
                                                   │
                   ┌───────────────────────────────┼───────────────────────────────┐
                   ▼                               ▼                               ▼
      [4. SPECIALIZED EXECUTION ENGINES]
         +───────────────────────+       +───────────────────────+       +───────────────────────+
         |     GRAPH ENGINE      |       |    PAYLOAD ENGINE     |       |  ENVIRONMENT ENGINE   |
         | - BFS/DFS Pathfinding |       | - Cryptographic Regex |       | - Absolute OS Paths   |
         | - Static Taint Flows  |       | - High-Density NER    |       | - Shell Context Reads |
         +─────────┬─────────────+       +─────────┬─────────────+       +─────────┬─────────────+
                   │                               │                               │
                   ▼                                ▼                               ▼
      [5. LOCAL DATA SOURCES]
         +───────────────────────+       +───────────────────────+       +───────────────────────+
         |  THE KNOWLEDGE GRAPH  |       |  THE PROJECT SANDBOX  |       | THE GLOBAL OS SYSTEM  |
         | - graph.json topology |       | - Staged file diffs   |       | - ~/.aws/credentials  |
         | - Environment tagging |       | - Jupyter cell JSON   |       | - kubectl active ctx  |
         +───────────────────────+       +───────────────────────+       +───────────────────────+

---

## 7. Specialized Execution Engine Architectures

### 7.1 The Graph Engine (Semantic Traces)
Evaluates structural control-flow and data-flow reachability. It executes a **Directed Depth-First Search (DFS) with Path Accumulation**:
`Reachability(u, v) = path P = (u, e_1, w_1, e_2, ..., v)`
Where edge `e_n` is in `{CALLS, DEPENDS_ON, ASSIGNS, PASSES_ARG}`.

    [Staged File Paths]       [graphify-out/graph.json]
             │                            │
             ▼                            ▼
    +---------------------------------------------------+
    |                   GRAPH ENGINE                    |
    |                                                   |
    |  +---------------------------------------------+  |
    |  | 1. Incremental AST Node Patcher             |  |
    |  +---------------------------------------------+  |
    |                        │                          |
    |  +---------------------------------------------+  |
    |  | 2. DFS Reachability & Static Taint Tracker  |  |
    |  |    (Traces Edges: Non-Prod -> Prod Sinks)   |  |
    |  +---------------------------------------------+  |
    +------------------------┬--------------------------+
                             │
                             ▼
            [Violation Status JSON: Path Details]

### 7.2 The Payload Engine (Content Inspection)
Operates as a high-speed text stream processor decoupled from code context. To catch strings without false positives, the engine calculates the **Shannon Entropy (H)** of string tokens:
`H(X) = -sum( P(x_i) * log2(P(x_i)) )`

           [Git Index Raw Diffs (Staged Text)]
                            │
                            ▼
    +---------------------------------------------------+
    |                  PAYLOAD ENGINE                   |
    |                                                   |
    |                 [Route Router]                    |
    |                  /            \                   |
    |            *.ipynb             *.py, .env, etc    |
    |               ▼                    ▼              |
    |       +---------------+    +---------------+      |
    |       | Jupyter Cell  |    | Shannon       |      |
    |       | Unwrapper     |    | Entropy Eval  |      |
    |       +-------+-------+    +-------+-------+      |
    |               │                    │              |
    |               ▼                    ▼              |
    |       +------------------------------------+      |
    |       |  High-Density PII & Regex Scanner  |      |
    |       +------------------------------------+      |
    +-----------------------┬---------------------------+
                            │
                            ▼
            [Violation Status JSON: Secret/PII Hit]

### 7.3 The Environment Engine (Out-of-Band Profiling)
Functions as an OS profiling module, breaking out of the git directory to evaluate global state.
`SystemState = f(FilePresent(Path), RegexMatch(Lines), CommandOutput(String))`

     [OS File System]                [Terminal Process]
      (~/.aws, /etc)                  (kubectl / aws)
            │                                │
            ▼                                ▼
    +---------------------------------------------------+
    |                ENVIRONMENT ENGINE                 |
    |                                                   |
    |       +---------------+        +---------------+  |
    |       | Global Target |        | Runtime Shell |  |
    |       | Path Monitor  |        | State Sniffer |  |
    |       +-------+-------+        +-------+-------+  |
    |               │                        │          |
    |               ▼                        ▼          |
    |       +------------------------------------+      |
    |       |    State Validation Matrix Gate    |      |
    |       +------------------------------------+      |
    +-----------------------┬---------------------------+
                            │
                            ▼
            [Violation Status JSON: Env Config Hit]