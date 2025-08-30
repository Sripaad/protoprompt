12-Factor Agent Mapping (TinyContext)

This document adapts the 12-Factor App principles to agent systems and maps them to TinyContext.

1) Codebase
- Single repo, multiple deploys. Keep agents, orchestration, and context in one codebase. TinyContext organizes modules under tinycontext/.

2) Dependencies
- Explicit via pyproject.toml. No implicit global installs. Use pinned major versions and optional [dev] dependencies.

3) Config
- Strictly in the environment: .env, environment variables, tensorzero.toml. No secrets in code. CLI respects env.

4) Backing Services
- Treat LLM gateways, vector stores, and observability as attached resources. Swap via configuration (embedded vs HTTP TensorZero, future vector DBs).

5) Build, Release, Run
- Build: package installation. Release: git tag and release notes. Run: tinycontext CLI or examples. Keep these stages separate.

6) Processes
- Stateless orchestrators where possible. State lives in SharedContext and persistent storage, not process memory assumptions.

7) Port Binding
- CLI-first. When exposing services (future web UI), bind explicitly and configure via env.

8) Concurrency
- Async-first orchestration for multiple agents and concurrent LLM calls. Use AsyncTinyContextManager and AsyncTensorZeroClient.

9) Disposability
- Fast startup and graceful shutdown for clients and workflows. Avoid long-lived global state; persist context when needed.

10) Dev/Prod Parity
- Same code paths locally and in CI. Embedded TensorZero for local, HTTP gateway for prod, selected via env.

11) Logs
- Stream traces to stdout for CLI. Optionally send structured traces and episodes to TensorZero/ClickHouse for observability.

12) Admin Processes
- One-off scripts live in examples/ and tools/ (future). Migrations (e.g., dataclass_to_proto) are invocable and do not require app changes.

Agent-Specific Extensions
- Prompts-as-code: Templates live in tinycontext/prompts and are versioned.
- Tools-as-agents: External actions are wrapped in agents with clear capabilities.
- Memory: SharedContext provides per-agent memory and global state with optional persistence.
- Reproducibility: Episode IDs (uuid7) group runs for replay and analysis.

Gaps and Roadmap
- Pluggable vector stores as backing services
- Binary protobuf compilation for compact, fast storage
- Distributed process model for large agent fleets
