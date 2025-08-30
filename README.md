# TinyContext - Proto-First Multi-Agent Orchestration Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TensorZero](https://img.shields.io/badge/TensorZero-Enabled-green.svg)](https://tensorzero.com)

A lightweight, observable framework for orchestrating persistent AI agents with shared context, built on FSM principles and designed for protobuf serialization.

## 🎯 What is TinyContext?

TinyContext treats AI agents as **first-class citizens** with:
- **Persistent Identity** - Agents maintain state across sessions
- **Shared Context** - True collaboration through shared memory
- **Observable Behavior** - Every decision tracked via TensorZero
- **Emergent Intelligence** - Complex behaviors from simple rules

Think of it as "Kubernetes for AI Agents" - orchestrating fleets of specialized agents that collaborate to solve complex problems.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Your Application                   │
├─────────────────────────────────────────────────────┤
│              AsyncTinyContextManager                │
│         (Orchestrates multi-agent workflows)        │
├──────────────┬──────────────┬───────────────────────┤
│ ProtoFactory │ SharedContext │  AsyncTinyWorld FSM  │
│   (Agents)   │   (Memory)    │    (State Machine)   |
├──────────────┴──────────────┴───────────────────────┤
│               TensorZero Gateway                    │
│          (Observability & LLM Inference)            |
└─────────────────────────────────────────────────────┘
```

## ✨ Key Features

### 🤖 TinyPerson Agents
- **Proto-First Design** - Ready for serialization and sharing
- **Personality & Role** - Each agent has unique characteristics
- **Capabilities** - Declare what each agent can do
- **Templates** - Pre-built agent archetypes

### 🧠 Shared Context System
- **Global State** - Key-value store accessible by all agents
- **Message Passing** - Broadcast, direct, and handoff protocols
- **Agent Memory** - Per-agent working memory and history
- **Persistence** - Save and restore entire contexts

### 🔄 Async Execution
- **Concurrent Agents** - Multiple agents working in parallel
- **Non-blocking I/O** - Async LLM calls via TensorZero
- **Event-driven** - React to state changes and messages

### 📊 Full Observability
- **Episode Tracking** - Group related inferences with UUID v7
- **Execution Traces** - See every decision and handoff
- **Performance Metrics** - Track success rates and timing
- **ClickHouse Integration** - Professional-grade analytics

## 🚀 Quick Start

### Simple API (Recommended for beginners)

```bash
# Install with dependencies
pip install -e .
pip install openai

# Set your Groq API key for high-speed inference (preferred)
export GROQ_API_KEY=your-groq-api-key-here
# Or use OpenAI as fallback  
export OPENAI_API_KEY=your-openai-api-key-here

# Zero-config usage
python -c "
from tinycontext.simple import quick_start
import asyncio

async def demo():
    agent = quick_start()
    result = await agent.run('Hello world! What can you do?')
    print(result['output'])

asyncio.run(demo())
"
```

**Or use the CLI:**

```bash
# Interactive setup
tinycontext setup

# Quick execution
tinycontext quick "Analyze this data" --data '{"sales": [100, 200, 300]}'

# Interactive demo
tinycontext demo
```

### Full Framework Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/protoprompt.git
cd protoprompt

# Using uv (recommended)
uv venv
uv pip install -e .

# Or using pip
pip install -e .
```

### Set Up Environment

```bash
# Create .env file
cat > .env << EOF
GROQ_API_KEY=your-groq-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
TENSORZERO_MODEL=groq
ENABLE_OBSERVABILITY=true
EOF
```

### Run TensorZero (Optional - for observability)

```bash
# Start TensorZero with ClickHouse
docker-compose up -d

# TensorZero UI will be available at http://localhost:3000
```

## 📚 Usage Examples

### 🎯 Simple API Examples

#### Context Engineering Showcase

```python
from tinycontext.simple import ContextAgent

# Research Assistant with Context Selection
agent = ContextAgent(name="researcher")
await agent.initialize()

# Build knowledge base (Write Context)
await agent.add_context("ai_safety", "AI safety research focuses on...", ["ai", "safety"])
await agent.add_context("quantum_computing", "Quantum computing uses...", ["quantum", "tech"])

# Query with context selection (Select Context)
result = await agent.run(
    "What are the connections between AI safety and quantum computing?",
    context_strategy="select"  # Automatically selects relevant contexts
)

# Long conversation with compression (Compress Context) 
for query in ["What is AI safety?", "How does quantum computing work?", "What are the risks?"]:
    result = await agent.run(query, context_strategy="compress")

# Isolated analysis (Isolate Context)
await agent.create_isolated_context("security_analysis", {
    "threats": {"type": list}, 
    "risk_level": {"type": str}
})
result = await agent.run("Analyze security implications", context_strategy="isolate")
```

#### One-Line Task Execution

```python
from tinycontext.simple import run_quick_task

# Instant results
result = await run_quick_task("Summarize this text", data={"text": "Long document..."})
analysis = await run_quick_task("Find patterns", data={"numbers": [1,1,2,3,5,8]})
code_review = await run_quick_task("Review this code for security issues", data={"code": "..."})
```

### 🏗️ Full Framework Examples  

#### 1. Multi-Agent Orchestration

```python
import asyncio
from tinycontext.agents.proto_factory import ProtoFactory
from tinycontext.manager.async_context_manager import AsyncTinyContextManager

async def main():
    # Initialize manager
    manager = AsyncTinyContextManager()
    await manager.initialize()
    
    # Run a task
    result = await manager.run(
        task="Analyze customer feedback and suggest improvements",
        input_data={"feedback": ["Great product!", "Needs better docs"]}
    )
    
    print(f"Result: {result['output']}")
    print(f"Agents used: {result['agents_used']}")
    print(f"Handoffs: {result['handoff_count']}")

asyncio.run(main())
```

#### 2. Multi-Agent Collaboration with Shared Context

```python
from tinycontext.context.context_manager import ContextManager
from tinycontext.agents.proto_factory import ProtoFactory

async def collaborative_task():
    # Create context manager
    ctx_manager = ContextManager()
    factory = ProtoFactory()
    
    # Create shared context
    context = await ctx_manager.create_context("project_alpha")
    
    # Create specialized agents
    researcher = factory.create_agent(
        name="researcher",
        role="researcher", 
        capabilities=["search", "analyze"],
        template="research"
    )
    
    writer = factory.create_agent(
        name="writer",
        role="writer",
        capabilities=["write", "edit"],
        template="coding"
    )
    
    # Assign to context
    await ctx_manager.assign_agent(researcher, "project_alpha")
    await ctx_manager.assign_agent(writer, "project_alpha")
    
    # Agents collaborate through shared context
    await context.broadcast("researcher", "Found 3 key insights")
    await context.write_global("status", "research_complete")
    
    # Handoff task
    await context.handoff(
        "researcher", 
        "writer",
        "Create report from insights",
        {"insights": ["insight1", "insight2", "insight3"]}
    )
```

#### 3. RAG Pipeline (Emerging from Agents)

```python
from tinycontext.orchestration.rag_orchestrator import RAGOrchestrator

async def rag_query():
    orchestrator = RAGOrchestrator()
    await orchestrator.initialize()
    
    # RAG emerges from agent collaboration
    result = await orchestrator.answer_query(
        "What are the latest developments in quantum computing?",
        max_iterations=10,
        verbose=True
    )
    
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")
    print(f"Confidence: {result['confidence']:.0%}")
```

#### 4. Agent Persistence and Versioning

```python
from tinycontext.agents.proto_factory import ProtoFactory

async def agent_persistence():
    factory = ProtoFactory()
    
    # Create and save agent
    agent = factory.create_agent(
        name="data_analyst",
        role="analyst",
        persona="Expert at finding patterns in data"
    )
    
    # Save with version
    storage_id = await factory.save_agent(agent, version="1.0.0")
    
    # Create new version
    agent.capabilities.append("visualization")
    version_id = await factory.create_agent_version(
        "data_analyst",
        "1.1.0", 
        "Added visualization capability"
    )
    
    # List versions
    versions = await factory.list_agent_versions("data_analyst")
    
    # Export agent
    exported = await factory.export_agent("data_analyst", format="json")
```

#### 5. Workflow Execution

```python
from tinycontext.workflows.workflow_executor import WorkflowExecutor
from tinycontext.workflows.workflow_definition import (
    WorkflowDefinition, 
    StepDefinition
)

async def run_workflow():
    executor = WorkflowExecutor()
    await executor.initialize()
    
    # Define workflow
    workflow = WorkflowDefinition(
        name="data_pipeline",
        steps=[
            StepDefinition(
                name="collect",
                agent_role="collector",
                action="gather_data"
            ),
            StepDefinition(
                name="analyze",
                agent_role="analyst",
                action="process_data",
                depends_on=["collect"]
            ),
            StepDefinition(
                name="report",
                agent_role="writer",
                action="generate_report",
                depends_on=["analyze"]
            )
        ]
    )
    
    # Execute workflow
    result = await executor.execute_workflow(
        workflow,
        initial_input={"data_source": "api"}
    )
```

## 🧪 Testing

### Run All Tests

```bash
# Run the comprehensive test suite
uv run python test_abstraction_layer.py

# Or with pytest
pytest tests/
```

### Test Individual Components

```python
# Test storage
from tinycontext.storage.agent_store import AgentStorage

storage = AgentStorage()
await storage.store(agent)
retrieved = await storage.retrieve(storage_id)

# Test context
from tinycontext.context.shared_context import SharedContext

context = SharedContext()
await context.write_global("key", "value")
await context.broadcast("agent", "message")
```

## 📁 Project Structure

```
tinycontext/
├── agents/           # Agent definitions and management
│   ├── loader.py            # Base TinyPerson and Factory
│   ├── proto_factory.py     # Enhanced factory with proto support
│   └── rag_agents.py        # Specialized RAG agents
├── core/            # Core execution engines
│   ├── tiny_world.py        # Synchronous FSM
│   ├── async_tiny_world.py  # Async FSM
│   ├── react_loop.py        # ReAct pattern implementation
│   └── rag_world.py         # RAG-specific states
├── context/         # Shared context system
│   ├── shared_context.py    # Context and messaging
│   └── context_manager.py   # Multi-context management
├── storage/         # Persistence layer
│   └── agent_store.py       # Versioned agent storage
├── orchestration/   # High-level orchestrators
│   ├── workflow_executor.py # Workflow engine
│   └── rag_orchestrator.py  # RAG coordination
├── inference/       # LLM integration
│   └── tensorzero_client.py # TensorZero gateway
├── migration/       # Migration utilities
│   └── dataclass_to_proto.py # Convert existing agents
└── protos/          # Protobuf schemas
    ├── person.proto         # Agent definition
    ├── shared_context.proto # Context schema
    └── agent_storage.proto  # Storage format
```

## 🔧 Configuration

### TensorZero Configuration (`tensorzero.toml`)

```toml
[models.gpt4o_mini]
type = "openai"
model_name = "gpt-4o-mini"
api_key_location = "env:OPENAI_API_KEY"

[functions.tiny_reasoning]
type = "chat"
model = "gpt4o_mini"

[functions.tiny_action]
type = "chat"
model = "gpt4o_mini"

[observability]
type = "clickhouse"
url = "http://localhost:8123/tensorzero"
```

### Agent Templates

```python
# Create from template
agent = factory.create_agent(
    name="my_researcher",
    template="research",  # Uses pre-built template
    capabilities=["search", "analyze", "summarize"]
)

# Available templates:
# - research: Information gathering and analysis
# - coding: Software development tasks
# - manager: Task coordination and delegation
```

## 🎯 Common Use Cases

### 1. Customer Support Automation
```python
# Route → Research → Draft → Review → Send
support_team = ["router", "researcher", "writer", "reviewer"]
```

### 2. Data Analysis Pipeline
```python
# Collect → Clean → Analyze → Visualize → Report
data_team = ["collector", "cleaner", "analyst", "visualizer", "reporter"]
```

### 3. Content Generation
```python
# Research → Outline → Write → Edit → Publish
content_team = ["researcher", "outliner", "writer", "editor", "publisher"]
```

### 4. Code Review System
```python
# Analyze → Lint → Security → Performance → Summary
review_team = ["analyzer", "linter", "security_checker", "perf_analyzer", "summarizer"]
```

## 🚧 Advanced Features

### Episode Tracking
```python
# All related inferences grouped under one episode
import uuid_utils
episode_id = str(uuid_utils.uuid7())

result = await manager.run(
    task="Complex multi-step task",
    episode_id=episode_id  # Track in TensorZero UI
)
```

### Agent Migration
```python
from tinycontext.migration.dataclass_to_proto import AgentMigrator

migrator = AgentMigrator()
summary = await migrator.migrate_all(validate=True)
print(f"Migrated {summary['successful']} agents")
```

### Context Persistence
```python
# Save context
await context.save("/path/to/context.json")

# Load context
restored = SharedContext()
await restored.load("/path/to/context.json")
```

## 🐛 Debugging

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View TensorZero Traces
```bash
# Access TensorZero UI
open http://localhost:3000

# View episodes and traces
# Filter by episode_id to see full conversation flow
```

### Inspect Agent State
```python
# Get agent's current state
state = world.get_state_info()
print(f"State: {state['current_state']}")
print(f"Context: {state['context']}")

# View transition history
history = world.get_transition_history()
```

## 🤝 Contributing

We welcome contributions! Please see [CHECKPOINT.md](CHECKPOINT.md) for detailed architecture documentation.

### Development Setup
```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black tinycontext/
ruff check tinycontext/
```

## 📚 Documentation

- **[Simple API Guide](docs/SIMPLE_API.md)** - Complete guide to TinyContext Simple with context engineering
- **[CHECKPOINT.md](CHECKPOINT.md)** - Detailed architecture and design decisions
- **[Examples](examples/)** - Usage examples including Simple API demos
- [API Reference](docs/api.md) - Complete API documentation (coming soon)
- [12-Factor Agent Mapping](docs/12_FACTOR_AGENT.md) - How TinyContext aligns with 12-factor principles
- [MVP Plan](docs/MVP_PLAN.md) - Scope, deliverables, and acceptance criteria for the first release

### Troubleshooting
- Ensure Python 3.11+ and pip/uv are installed
- Create a .env from .env.example and set OPENAI_API_KEY
- If observability services are not running, set use_embedded=True for AsyncTensorZeroClient or run docker-compose up -d

## 🗺️ Roadmap

### Near Term
- [ ] Real vector database integration (Chroma/Pinecone)
- [ ] Emotion and sentiment modeling
- [ ] Binary protobuf compilation
- [ ] Distributed agent execution

### Long Term
- [ ] Visual workflow designer
- [ ] Agent marketplace
- [ ] Auto-scaling agent pools
- [ ] Cross-language agent support

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [TensorZero](https://tensorzero.com) for observability
- Inspired by FSM patterns and emergent behavior principles
- Community contributions and feedback

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/protoprompt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/protoprompt/discussions)
- **Documentation**: [Read the Docs](https://protoprompt.readthedocs.io) (coming soon)

---

*"In the land of AI, the tiny person with memory is king."* - The TinyContext Philosophy