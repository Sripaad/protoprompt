TinyContext MVP Plan

Goal
- Ship a small, usable MVP that demonstrates context engineering and multi-agent orchestration, is easy to run locally, and is designed to scale with minimal refactors.

Scope (MVP)
- CLI: tinycontext run to execute a task with optional input JSON and verbose trace output.
- Context: SharedContext with global state, messages, and per-agent memory persisted optionally to disk.
- Orchestration: Single-agent and multi-agent flows via TinyContextManager and AsyncTinyContextManager.
- LLM Integration: TensorZero client (embedded or HTTP) with episode_id support.
- Examples: Two runnable examples that showcase capability and extension points.
  - Multi-agent handoff and shared context
  - RAG-style research orchestration with iteration and confidence
- Documentation: Quickstart, configuration, examples usage, extension points.

Non-Goals (for MVP)
- Distributed execution across processes or hosts
- External vector DB integrations beyond simple stubs
- Compiled protobuf binaries and code-gen
- Advanced safety, grounding, or tool sandboxing

Success Criteria
- One command install and run locally (pip install -e . then tinycontext run ...)
- Both examples run end-to-end with sensible output using an API key set via .env
- Clear docs with copy-paste commands and expected outputs
- Simple extension: a developer can add a new agent template and see it listed via CLI

Deliverables
- Working CLI entrypoint: tinycontext
- Two examples in examples/ with concise READMEs inline in file headers
- Updated README with Quickstart and Docs links
- Docs: 12-Factor Agent mapping and this MVP plan

Backlog → To-Do
1) Developer Experience
   - [ ] Confirm Python 3.11+ and pip install -e . path works on a clean machine
   - [ ] Add Troubleshooting section to README (common errors, missing API keys)
   - [ ] Provide .env.example with documented keys

2) CLI polish
   - [ ] tinycontext agents prints templates sourced from prompts/sample_prompts.yaml as well
   - [ ] tinycontext run --session stores and loads session traces reliably
   - [ ] Add tinycontext init to create a minimal project scaffold (already present) and verify outputs

3) Context engineering
   - [ ] Provide a short “Context Assembly” guide: how SharedContext is built and what goes into prompts
   - [ ] Add a code snippet showing how to plug custom context providers (files, environment, prior runs)

4) Examples
   - [ ] Example 1: Multi-agent handoff (examples/multi_agent.py) – verify and document expected output
   - [ ] Example 2: RAG orchestrator (examples/rag_tinyperson_demo.py) – verify simple and multi-hop runs
   - [ ] Optional: Async concurrency demo (examples/async_multi_agent_demo.py) documented as bonus

5) Observability (optional for MVP, recommended)
   - [ ] docker-compose up -d brings up TensorZero and ClickHouse
   - [ ] README includes how to switch AsyncTensorZeroClient to use embedded vs HTTP gateway
   - [ ] Show how to set and use episode_id (uuid7)

6) Packaging and Release
   - [ ] Ensure pyproject has console_scripts entry (already present)
   - [ ] Tag 0.0.1 and produce a GitHub release (manual step)
   - [ ] Changelog entry describing MVP scope

7) Testing and CI (lightweight)
   - [ ] Smoke test: run the two examples in CI with mocked LLM
   - [ ] Unit tests for SharedContext basic operations
   - [ ] Lint/format checks via ruff/black

Sequencing (suggested)
- Day 1: Verify examples, fix obvious gaps, polish CLI output, add docs skeleton
- Day 2: Add context assembly doc, .env.example, troubleshooting; finalize README Quickstart
- Day 3: Observability instructions, basic tests, release prep

Open Questions
- Preferred default model/provider? (OpenAI via TensorZero, Anthropic via LiteLLM, local via Ollama)
- Interface priorities? (CLI only for MVP vs simple web UI)
- Are Docker and TensorZero required for MVP, or optional?

Risks and Mitigations
- Dependency friction (TensorZero): keep embedded gateway as default; document HTTP path
- API rate/keys: provide clear env var configuration and fallbacks
- Example drift: pin example code to current APIs and assert minimal outputs

Next Steps (blocking decisions)
- Confirm provider defaults and whether to keep observability optional or required
- Approve example set and acceptance criteria
