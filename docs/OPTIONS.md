Implementation Options and Trade-offs

Language/Runtime
- Python (current): Fast prototyping, rich ecosystem, async supported. Best developer ergonomics for MVP.
- Node/TypeScript: Strong tooling for web UI, good SDK coverage, more work to port current code.

LLM Provider Abstraction
- TensorZero (current): Centralized config, observability, function routing; requires local services for full UI.
- Direct SDKs (OpenAI/Anthropic): Fewer moving parts; loses unified observability; add your own tracing.
- LiteLLM: Vendor-agnostic wrapper; compatible with both local and hosted providers; adds another dependency.

Model Hosting
- Hosted APIs (default): Simple and reliable, costs may apply.
- Local (Ollama/vLLM): Private and offline; heavier setup; lower context windows depending on models.

Memory and Retrieval
- In-memory/JSON (current): Simple and easy to inspect; limited scale.
- SQLite/duckdb: Lightweight local persistence without external services.
- Vector DBs (Chroma, Qdrant, Pinecone): Scaling retrieval with embeddings/tracing; adds operational overhead.

Orchestration Interface
- CLI-first (current): Simple and scriptable; great for MVP and dev workflow.
- Web UI (later): Friendly demos and observability UX; build after CLI stabilizes.

Packaging and Distribution
- pip package + console_scripts (current): Easiest to install and run.
- Docker image: Reproducible environment; larger footprint; good for demos and CI.

Recommendation for MVP
- Keep Python + TensorZero client. Make observability optional (embedded by default).
- Ship CLI + examples; defer web UI.
- Keep memory JSON-based; expose interfaces to swap in a vector store later.
