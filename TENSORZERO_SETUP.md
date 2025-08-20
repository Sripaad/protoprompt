# TensorZero Setup Guide for TinyContext

## Prerequisites

1. Docker and Docker Compose installed
2. OpenAI API key

## Setup Instructions

### 1. Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Enable observability for embedded gateway
export ENABLE_OBSERVABILITY=true
export TENSORZERO_CLICKHOUSE_URL="http://chuser:chpassword@localhost:8123/tensorzero"
```

### 2. Start TensorZero Services

```bash
# Start ClickHouse, TensorZero Gateway, and UI
docker compose up -d
```

This will start:
- **ClickHouse** database on port 8123
- **TensorZero Gateway** on port 3000
- **TensorZero UI** on port 4000

### 3. Verify Services

Check that all services are running:
```bash
docker compose ps
```

Access the TensorZero UI:
```
http://localhost:4000
```

### 4. Using TinyContext with TensorZero

#### Option A: Embedded Gateway (Python only)
```python
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient

# Uses embedded gateway - no Docker required
client = AsyncTensorZeroClient(use_embedded=True)
await client.initialize()
```

#### Option B: HTTP Gateway (via Docker)
```python
from tinycontext.inference.tensorzero_client import AsyncTensorZeroClient

# Uses HTTP gateway running in Docker
client = AsyncTensorZeroClient(use_embedded=False)
await client.initialize()
```

## Running Examples

### Async Multi-Agent Demo
```bash
uv run python examples/async_multi_agent_demo.py
```

### Async TensorZero Examples
```bash
uv run python examples/async_tensorzero_example.py
```

## Configuration

The TensorZero configuration is in `tensorzero.toml`:
- **Functions**: Define AI tasks (reasoning, action, selection)
- **Variants**: Implementation details for each function
- **Model**: Currently uses `openai::gpt-4o-mini`

## Monitoring

View real-time metrics and traces in the TensorZero UI:
1. Navigate to http://localhost:4000
2. Explore function calls, latencies, and token usage
3. Analyze agent interactions and handoffs

## Stopping Services

```bash
docker compose down
```

To also remove data volumes:
```bash
docker compose down -v
```

## Troubleshooting

### Gateway Connection Issues
- Ensure OPENAI_API_KEY is set
- Check Docker logs: `docker compose logs tensorzero-gateway`
- Verify config file: `docker compose exec tensorzero-gateway cat /config/tensorzero.toml`

### ClickHouse Issues  
- Check ClickHouse logs: `docker compose logs clickhouse`
- Verify database is accessible: `curl http://localhost:8123/ping`

### UI Not Loading
- Check UI logs: `docker compose logs tensorzero-ui`
- Ensure gateway is healthy: `curl http://localhost:3000/health`