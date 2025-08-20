# TinyContext - FSM-Based AI Agent Orchestration (MVP v0.0.1)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight framework for orchestrating AI agents using Finite State Machines (FSM) and TensorZero for LLM inference.

## 🏗️ Architecture

```
                ┌───────────────────────────────┐
                │      Your Application         │
                │  (Task queue, UI, endpoint)   │
                └────────────┬──────────────────┘
                             │
                ┌────────────▼────────────┐
                │    TinyContextManager   │  ◀── (🧠 core abstraction)
                └─────┬───────┬───────────┘
                      │       │
        ┌─────────────▼──┐ ┌──▼────────────────┐
        │ TinyFactory     │ │ TinyWorld (FSM)   │
        │ (loads agents)  │ │ (5-state machine) │
        └────────────────┘ └────────────────────┘
                      │
          ┌───────────▼───────────┐
          │   TinyPerson Agents   │  (Protobuf defined)
          └───────┬───────────────┘
                  │
          ┌───────▼────────┐
          │ TensorZero LLM │  (Inference Layer)
          └────────────────┘
```

## ✨ Key Components

### 🧩 TinyPerson (Agent Node)
- Defined using Protocol Buffers
- Stateless agents with roles (strategist, planner, analyzer)
- ReAct-style reasoning and action loops

### 🔁 TinyWorld (FSM Engine)
5-state finite state machine:
- **IDLE** - Waiting for input
- **THINKING** - Processing/reasoning
- **ACTING** - Executing action
- **HANDING_OFF** - Transferring to another agent
- **ERROR** - Error state

### 🧠 TinyContextManager
Central orchestrator that:
- Selects appropriate agents
- Manages FSM transitions
- Coordinates LLM calls via TensorZero
- Tracks execution traces

### ⚡ TensorZero Integration
- Primary model: `openai/gpt-5-chat`
- Configurable via `tensorzero.toml`
- Functions: `tiny_reasoning`, `tiny_action`

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
uv venv
uv pip install -e .

# Using pip
pip install -e .
```

### Initialize Configuration

```bash
tinycontext init
```

This creates:
- `agents/` - Agent definitions
- `prompts/` - Prompt templates
- `sessions/` - Session storage

### Run a Task

```bash
# Simple task
tinycontext run "Create a strategy for improving user retention"

# With input data
tinycontext run "Analyze this data" -i '{"metrics": [1, 2, 3]}'

# Verbose mode with trace
tinycontext run "Plan a product launch" -v

# Use specific agent
tinycontext run "Break down this problem" -a strategist
```

### CLI Commands

```bash
# List available agents
tinycontext agents

# List sessions
tinycontext sessions

# Replay a session
tinycontext replay <session-id>
```

## 📂 Project Structure

```
tinycontext/
├── agents/
│   ├── person.proto      # Protobuf schema
│   └── loader.py         # Agent factory
├── core/
│   ├── tiny_world.py     # FSM implementation
│   └── react_loop.py     # ReAct pattern
├── manager/
│   └── context_manager.py # Central orchestrator
├── inference/
│   └── tensorzero_client.py # LLM integration
├── sessions/
│   └── session_manager.py # Session tracking
├── prompts/
│   └── sample_prompts.yaml # Prompt templates
├── cli.py                # CLI interface
├── tensorzero.toml       # TensorZero config
└── pyproject.toml        # Package config
```

## 🔧 Configuration

### Agent Definition (YAML/JSON)

```json
{
  "name": "strategist",
  "role": "strategist",
  "persona": "A strategic thinker who breaks down complex problems",
  "prompts": {
    "system": "You are a strategic analyst...",
    "reasoning_template": "Given: {input}...",
    "action_template": "Based on analysis: {action}"
  }
}
```

### TensorZero Configuration

```toml
[[functions]]
name = "tiny_reasoning"
model = "gpt-5-chat"
prompt_template = "You are a TinyPerson. {{input}}"
```

## 🧪 Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black tinycontext/
ruff check tinycontext/
```

### Compile Protobuf (Optional)

```bash
# Install protoc compiler
brew install protobuf  # macOS

# Compile proto files
protoc --python_out=. tinycontext/agents/person.proto
```

## 📋 MVP Checklist

- ✅ Protobuf schema for TinyPerson
- ✅ TinyFactory agent loader
- ✅ TinyWorld FSM with 5 states
- ✅ TinyContextManager orchestrator
- ✅ TensorZero client integration
- ✅ CLI runner
- ✅ Session management
- ✅ Sample prompts
- ✅ pyproject.toml with uv support

## 🗺️ Future Enhancements

- [ ] LangGraph integration
- [ ] Plugin system for tools/memory
- [ ] Vector store integration
- [ ] Multi-agent swarm coordination
- [ ] Web UI interface
- [ ] Real TensorZero API integration

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with TensorZero for LLM inference
- Uses Protocol Buffers for agent definitions
- FSM pattern for predictable agent behavior