# Prompt→Workflow System — Technical Specification (v1.1) - Deviated | TODO: Redefine and align on usecase

> **Purpose.** A modular, typed, and observable orchestration system that turns prompts (or structured requests) into deterministic, versioned workflows. It uses **Tensor0** as the high‑performance orchestrator and **Protobuf** to define agents, steps, types, and policies. Initial scope: **data pipelines**, **content generation**, **API chaining**. Extensible to **multi‑agent** and **deep research** workflows.

---

## 0) Change Log (since v0 draft)

* **Agent state/secrets:** Added explicit lifecycle, session/token management, secret scoping, and network allowlists.
* **Typed I/O:** Introduced `DataType`, `DataSpec`, `ValueRef`, adapters, and URI‑based large payloads.
* **Error model:** Failure classes, retries with backoff/jitter, on‑error directives (RETRY/CONTINUE/FALLBACK/COMPENSATE), Saga compensation, DLQ + repro packs.
* **Scalability:** Concurrency, token‑bucket rate limiting (per provider/model), backpressure, and quotas.
* **Versioning:** Immutable semver’d specs, blue/green routing, spec hashing, and run→spec provenance.
* **Prompt→Spec bridge:** Prompt‑Parser Agent with JSON schema, confidence/ambiguity, deterministic routing.
* **Validation/Monitoring:** Static type/DAG validation, resource estimation, rich run metadata, debugger CLI.
* **Config layer:** Env profiles, secret providers, and policy bundles.

---

## 1) Executive Summary

* **What:** A Python package that executes **Protobuf‑defined workflows** via **Tensor0**. Each workflow is a DAG of **agent steps** with typed inputs/outputs, retries, resource/rate policies, and strong observability.
* **Why:** Determinism, composability, and performance for business workflows that blend LLM calls, data transforms, and external APIs.
* **How:**

  * **Specs** describe *what* to run (agents, steps, types).
  * **Engine** plans/validates/executes the DAG, calls agents via Tensor0, enforces limits, and records traces.
  * **Agents** are plugins with declared capabilities, secrets, and resource appetites.
  * **Prompt‑Parser** converts NL prompts into `{ workflow, inputs }` for deterministic execution.

---

## 2) Scope & Non‑Goals

**In‑scope (v1):**

* Triggered/UI workflows (no mid‑run user interaction), linear or mildly parallel DAGs.
* LLM calls, REST API calls, simple data transforms, artifact storage.
* Strong typing, validation, retries, rate limits, secrets, and audit.

**Non‑goals (v1):**

* Long‑running agents with autonomous background behavior.
* Real‑time multi‑agent dialogues/negotiation.
* Distributed compute scheduling (beyond Tensor0 concurrency).

---

## 3) Target Workflows & Use Cases

1. **Data pipelines**: CSV/Parquet ingestion → clean/filter → summary report.
2. **Content generation**: outline → draft → refine → SEO → publish via CMS API.
3. **API chaining**: search KB → LLM answer → ticket creation.
4. **(Future) Multi‑agent research**: researcher/critic/writer loop with shared memory.

---

## 4) Architecture Overview

**Layers**

1. **Input**: NL prompt or structured JSON. Prompts go through Prompt‑Parser Agent → structured invocation.
2. **Workflow Engine**: loads/validates `WorkflowSpec`, plans DAG, enforces policies, coordinates agents.
3. **Orchestrator (Tensor0)**: executes step calls; provides traces/metrics and model/tool adapters.
4. **Agent Layer**: pluggable agents (LLM, API, DataProc, Aggregator, Decision). Lifecycle: init→execute→teardown.
5. **Runtime Services**: config (env profiles), secrets, artifact store (CAS URIs), cache, schema registry, metrics/logging.

**Core runtime objects**

* `RunContext(run_id, workflow_version, secrets_view, caches, ratelimiters)`
* `StepContext(step_id, retry_count, deadlines, trace_id)`
* `AgentInstance(config, required_secrets, ratelimit_bucket)`

---

## 5) Type System (Protobuf)

```protobuf
syntax = "proto3";

enum DataType {
  DT_UNSPECIFIED = 0;
  DT_TEXT = 1;   // UTF-8 text
  DT_JSON = 2;   // JSON string (validated by optional schema)
  DT_BYTES = 3;  // opaque bytes (mime via metadata)
  DT_URI = 4;    // external or content-addressed URIs
  DT_TABLE = 5;  // Arrow/Parquet (schema via metadata)
  DT_IMAGE = 6;  DT_AUDIO = 7;  DT_VIDEO = 8;
  DT_NUMBER = 9; DT_BOOL = 10;
}

message DataSpec {
  DataType type = 1;
  string format = 2;                    // e.g., "markdown", "csv", "parquet"
  map<string,string> metadata = 3;      // e.g., {"json_schema_uri": "..."}
}

message ValueRef {
  oneof value {
    string text = 1;
    string json = 2;
    bytes  bytes = 3;
    string uri = 4;
    double number = 5;
    bool   bool = 6;
  }
  DataSpec spec = 10;
}

message IOBinding {
  string from = 1;                 // "$input.name" | "$step.<id>.<out>" | "$const" | "$secret.name"
  ValueRef const_value = 2;        // required if from == "$const"
  DataSpec expect = 3;             // required type; engine enforces/adapts
}

message StepIO {
  map<string, IOBinding> inputs = 1;
  map<string, DataSpec> outputs = 2;  // declared names and types
}
```

**Rules**

* Large payloads use **DT\_URI** (e.g., `cas://sha256/...`, `s3://...`).
* Tables prefer Arrow/Parquet with schema URI.
* Engine auto‑inserts *adapters* (e.g., `URI(csv)→TABLE`) when safe.

---

## 6) Workflow Specification (Protobuf)

```protobuf
enum FailureClass { F_UNKNOWN = 0; F_TRANSIENT = 1; F_PERMANENT = 2; }

enum OnErrorAction {
  OE_FAIL = 0;
  OE_RETRY = 1;
  OE_CONTINUE = 2;        // propagate null/empty output
  OE_FALLBACK_STEP = 3;   // jump to fallback_step_id
  OE_COMPENSATE = 4;      // run compensation then FAIL/CONTINUE
}

message RetryPolicy {
  int32 max_attempts = 1;
  int32 backoff_ms = 2;
  double backoff_multiplier = 3;
  int32 jitter_ms = 4;
  repeated string retry_on = 5;  // e.g., "F_TRANSIENT", "429", "ECONNRESET"
}

message ErrorHandling {
  OnErrorAction action = 1;
  string fallback_step_id = 2;
  string compensation_step_id = 3;
}

message ResourcePolicy {
  int32 cpu_milli = 1;   // hints
  int32 mem_mb = 2;
  int32 timeout_ms = 3;  // hard per-step deadline
}

message RateLimitSpec {
  string bucket = 1;     // e.g., "openai:gpt-5", "provider:acct-123"
  int32 rpm = 2;         // requests/min
  int32 tpm = 3;         // tokens/min (LLMs)
}

message AgentSpec {
  string id = 1;
  string kind = 2;                    // registry name (e.g., "csv_to_table")
  map<string,string> config = 3;      // non-secret config
  repeated string secrets = 4;        // logical secret names required
  string ratelimit_bucket = 5;        // optional
}

message LLMCall { string prompt_template = 1; map<string,string> params = 2; }
message APICall { string endpoint = 1; string method = 2; string body_template = 3; }
message DataTransform { string operation = 1; }

message Step {
  string id = 1;
  string agent_id = 2;
  StepIO io = 3;
  oneof action {
    LLMCall llm = 10;
    APICall api = 11;
    DataTransform xform = 12;
  }
  RetryPolicy retry = 20;
  ErrorHandling on_error = 21;
  ResourcePolicy resources = 22;
  bool cacheable = 23;
}

message ValidationRules { bool require_declared_outputs = 1; }

message WorkflowSpec {
  string name = 1; string version = 2; string spec_hash = 3;
  map<string, DataSpec> inputs = 4;
  map<string, DataSpec> outputs = 5;
  repeated AgentSpec agents = 6;
  repeated Step steps = 7;
  ValidationRules validation = 8;
}
```

---

## 7) Agents

**Concepts**

* **Lifecycle:** `init(ctx)` → `execute(ctx, inputs)` → `teardown(ctx)`.
* **Declarations:** `input_specs`, `output_specs`, `required_secrets`, `ratelimit_bucket`.
* **State:** sessions (HTTP, DB), token refresh, connection pools.
* **Isolation:** optional subprocess/container profiles for DataProc code.

**Registry pattern (Python)**

```python
AGENTS = {}

def register_agent(name):
    def deco(cls):
        AGENTS[name] = cls
        return cls
    return deco

class BaseAgent:
    input_specs: dict; output_specs: dict
    required_secrets: list[str] = []
    ratelimit_bucket: str | None = None
    def __init__(self, config: dict, runtime):
        self.config, self.runtime = config, runtime
    def init(self, ctx): ...
    async def execute(self, ctx, inputs: dict) -> dict: ...
    def teardown(self, ctx): ...
```

**Examples**

* `csv_to_table`: `URI(csv)` → `URI(parquet)` (via pandas/pyarrow).
* `llm_generate`: prompt\_template + inputs → text (Tensor0 inference).
* `http_call`: endpoint/method/body → HTTP response JSON/text.

---

## 8) Orchestration (Tensor0)

* Each workflow run = Tensor0 **episode**; each step = an action with trace/span.
* **Latency/scale:** sub‑ms orchestration overhead; concurrent steps when independent.
* **Features leveraged:** tracing, model/tool adapters, retries/timeouts, provider routing, caching (if available).

---

## 9) Engine

**Responsibilities**

* Load/validate spec; compute `spec_hash` and sign run metadata.
* Plan DAG; insert adapters; schedule steps (topological order + parallel where possible).
* Enforce rate/resource/timeouts; classify errors; apply OnError policy; run compensations; emit DLQ + repro packs.
* Persist artifacts under content‑addressed URIs; collect outputs; return deterministic result.

**Pseudocode (async)**

```python
async def run_workflow(spec, user_inputs, settings):
    run = new_run(spec)
    validate_inputs(spec, user_inputs)
    plan = plan_dag(spec)
    pool = AgentPool(spec, settings)
    ctx = RunContext(settings, spec, run)

    async def exec_step(step):
        sctx = StepContext(run, step)
        bound = await materialize(step.io.inputs, ctx)
        try:
            with rate_limiter(step):
                agent = pool.get(step.agent_id)
                out = await retry(agent.execute, step.retry, sctx, bound)
        except PermanentError as e:
            return await handle_error(step, sctx, e)
        await persist(step.io.outputs, out, ctx)
        return out

    await execute_topologically(plan, exec_step)
    return collect_outputs(spec, ctx)
```

---

## 10) Prompt‑Parser Agent

**Schema (contract)**

```json
{"type":"object","required":["workflow","inputs","confidence","ambiguities"],
 "properties":{"workflow":{"type":"string"},"inputs":{"type":"object"},
 "confidence":{"type":"number","minimum":0,"maximum":1},
 "ambiguities":{"type":"array","items":{"type":"string"}}}}
```

**Routing**: if `confidence ≥ τ` → run; else return a structured **clarification request** to caller (no mid‑run prompts in v1).
**Implementation**: LLM with function‑calling to the schema; validate JSON; map to `WorkflowSpec.inputs`.

---

## 11) Configuration & Secrets

* Pydantic **Settings** with profiles: `dev`, `staging`, `prod`.
* Secret providers chain: env → file → cloud secret manager (AWS/GCP/Vault).
* Specs refer to **logical resources** (e.g., `service:crm_api`) resolved by env config.
* Network allowlists per agent class; enforced before egress.

---

## 12) Validation & Planning

* **Static validation**: input presence/types, resolvable bindings, acyclic DAG, adapters available.
* **Resource estimation**: sum of timeouts vs. global budget; heuristic cost estimates for LLM tokens.
* **Planning**: topo sort, merge independent branches for parallel exec; cache reuse.

---

## 13) Error Handling & Recovery

* **Classes**: transient (timeouts, 5xx), permanent (4xx/validation), unknown.
* **Policies**: retry w/ backoff+jitter; compensation (Saga) for side‑effects; fallback steps; continue with null outputs; DLQ with repro pack.
* **Idempotency**: keys per step for safe retries (e.g., POST dedup).

---

## 14) Observability & Debugging

* **Metrics**: `workflow_run_latency`, `step_latency`, `retry_count`, `success_rate`, `token_usage`, `cache_hit_rate`.
* **Tracing**: propagate `run_id/step_id` into Tensor0 spans.
* **Logs**: structured JSON; input/output **fingerprints** (hashes) + redacted snippets.
* **Repro Pack**: `{spec, inputs, config_snapshot, redacted_artifacts, trace_ids}`; debugger CLI replays locally.

---

## 15) Versioning & Deployment

* **Immutable** `WorkflowSpec.version` (semver); **spec\_hash** checksum.
* **Blue/Green** routing at engine: percentage or label‑based.
* **Provenance**: all run records store `(name, version, spec_hash)`.
* **Migration**: new specs can read artifacts from older runs via adapters.

---

## 16) Security Model

* **Least‑privilege** secret scopes bound to agent classes.
* **Sandbox** DataProc agents (subprocess/container, seccomp where available).
* **Content safety** hooks before external publication (regex/allow‑deny lists).
* **Audit** trail: signed, append‑only.

---

## 17) API Surfaces

**CLI**

* `ptw init` — create skeleton project/spec.
* `ptw validate <spec.yaml>` — type/DAG checks.
* `ptw run <spec.(yaml|json|pb)> --inputs inputs.json` — execute.
* `ptw parse "<prompt>"` — Prompt‑Parser → JSON.
* `ptw inspect <run_id>` — show traces/metrics.
* `ptw replay <repro.zip>` — local debugger.

**Python SDK**

```python
from ptw import load_spec, run
spec = load_spec("examples/sales_csv_summary.yaml")
result = run(spec, inputs={"csv_uri": "file:///.../sales.csv"})
print(result["summary_text"])  # markdown
```

---

## 18) Example Workflow (CSV → summary → POST)

**YAML (compiles to Protobuf)**

```yaml
name: sales_csv_summary
version: 1.0.0
inputs:
  csv_uri: {type: URI, format: csv}
outputs:
  summary_text: {type: TEXT, format: markdown}

agents:
  - id: csv
    kind: csv_to_table
  - id: llm
    kind: llm_generate
    config: { model: "gpt-5" }
    secrets: [ "openai_api_key" ]
    ratelimit_bucket: "openai:gpt-5"
  - id: post
    kind: http_call
    secrets: [ "report_api_token" ]

steps:
  - id: to_table
    agent_id: csv
    io:
      inputs: { csv_uri: { from: "$input.csv_uri", expect: {type: URI, format: csv} } }
      outputs: { table: { type: TABLE, format: parquet } }
    retry: { max_attempts: 2, backoff_ms: 250, retry_on: ["F_TRANSIENT"] }

  - id: summarize
    agent_id: llm
    io:
      inputs:
        table_uri: { from: "$step.to_table.table", expect: {type: URI, format: parquet} }
    llm:
      prompt_template: |
        Summarize this sales table URI: {{ table_uri }} as markdown bullets.
    retry: { max_attempts: 3, backoff_ms: 500, backoff_multiplier: 2.0 }

  - id: publish
    agent_id: post
    io:
      inputs:
        url: { from: "$const", const_value: { text: "https://api.example.com/report", spec: {type: TEXT} } }
        body: { from: "$step.summarize.text", expect: {type: TEXT, format: markdown} }
    api: { endpoint: "{{ url }}", method: "POST", body_template: "{{ body }}" }
    on_error: { action: OE_CONTINUE }
```

---

## 19) Repository Scaffold (proposed)

```
ptw/
  pyproject.toml
  src/ptw/
    __init__.py
    cli.py
    config.py
    engine/
      __init__.py
      runner.py
      validator.py
      planner.py
      ratelimit.py
      errors.py
    agents/
      __init__.py
      registry.py
      csv_to_table.py
      llm_generate.py
      http_call.py
      adapters/
        __init__.py
        csv_to_parquet.py
    io/
      __init__.py
      artifacts.py
      secrets.py
  proto/
    ptw.proto
  examples/
    sales_csv_summary.yaml
    input.json
  tests/
    test_smoke.py
  README.md
```

---

## 20) PoC Plan (first pass)

1. **Scaffold repo** (files above) with stubs + minimal implementations.
2. **Proto v1** and loader (YAML→Protobuf conversion or direct JSON to Python dataclasses for PoC).
3. **Three agents**: `csv_to_table` (pandas/pyarrow), `llm_generate` (Tensor0 client stub), `http_call` (httpx).
4. **Engine MVP**: validation, topo planner, async runner, retries/timeouts, local CAS artifacts.
5. **Prompt‑Parser**: function‑call JSON schema; CLI route.
6. **Observability**: structured logs, run/step IDs, repro packs on failure.

---

## 21) Testing & QA

* **Unit**: validator, adapters, ratelimiters, error classification.
* **Golden**: example workflow outputs; markdown snapshot tests.
* **Contract**: ensure agents obey declared I/O specs.
* **Chaos**: induced timeouts/429 to validate retries and backoff.
* **Perf**: baseline step overhead, parallel step scaling.

---

## 22) Roadmap

**Near‑term**: Saga compensation, blue/green router, richer adapters, schema registry integration.
**Mid‑term**: conditional branches/loops in spec, shared memory, Planner‑in‑the‑loop agent.
**Long‑term**: interactive multi‑agent runs, multi‑tenant isolation, formal policy language (OPA/Rego) for network/secret access.

---

## 23) Glossary

* **Adapter**: micro‑step that converts one typed value to another (e.g., CSV→Parquet).
* **CAS**: content‑addressed storage; URIs keyed by content hash.
* **DLQ**: dead‑letter queue for failed runs with repro artifacts.
* **Saga**: pattern for compensating actions when a workflow partially fails.

---

### End of v1.0 Spec
