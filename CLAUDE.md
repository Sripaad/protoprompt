# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TinyContext is a multi-agent framework for creating AI agents with rich personas, ReAct-style reasoning, and persistent context management. The system is inspired by Microsoft's TinyTroupe but focuses on practical context management and multi-agent orchestration.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
uv sync

# Install in development mode with all extras
uv pip install -e ".[dev,vector]"

# Setup PostgreSQL with pgvector
# On macOS with Homebrew:
brew install postgresql@15
brew services start postgresql@15
brew install pgvector

# Create database
createdb tinycontext
psql -d tinycontext -c "CREATE EXTENSION vector;"
```

### Running the Application
```bash
# Run CLI commands
uv run python -m tinycontext.main --help

# Run specific agent
uv run python -m tinycontext.main run --agent "Alice" --interactive

# Run tests
uv run pytest
uv run pytest --cov=tinycontext

# Code quality checks
uv run black tinycontext/
uv run ruff check tinycontext/
uv run mypy tinycontext/
```

### Package Management
```bash
# Add production dependency
uv add <package-name>

# Add development dependency
uv add --dev <package-name>

# Update all dependencies
uv sync --upgrade

# Generate protobuf files
protoc --python_out=. tinycontext/agents/schemas/*.proto
```

## Implementation Plan

### Phase 1: Core Foundation
1. **Project Structure** - Create package directories and __init__ files
2. **Dependencies** - Update pyproject.toml with all required packages
3. **Base Classes** - Implement TinyPerson base class with minimal functionality

### Phase 2: Agent System
1. **Agent Factory** - TinyPersonFactory for creating agents
2. **Persona System** - Rich persona attributes and configuration
3. **Prompting** - System prompt generation and management

### Phase 3: ReAct Implementation
1. **Reasoning Loop** - Think → Act → Reflect cycle
2. **Response Types** - Structured responses with reasoning traces
3. **Context Integration** - Incorporate context into reasoning

### Phase 4: Session Management
1. **Session Manager** - Orchestrate multi-agent conversations
2. **Context Builder** - Aggregate and manage conversation context
3. **State Persistence** - Save/load session states

### Phase 5: Serialization & CLI
1. **Protobuf Schemas** - Define agent and session schemas
2. **Serialization** - Implement save/load functionality
3. **CLI Interface** - Click-based command line tools

### Phase 6: Advanced Features
1. **Vector Memory** - pgvector integration for semantic memory search
2. **Tool Use** - Allow agents to use external tools
3. **Async Operations** - Support concurrent agent operations

## Architecture Guidelines

### Database Schema (pgvector)
```sql
-- Agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    persona JSONB,
    system_prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Memories table with vector embeddings
CREATE TABLE memories (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id),
    content TEXT,
    embedding vector(1536),  -- OpenAI ada-002 dimensions
    metadata JSONB,
    importance FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    context TEXT,
    state JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Interactions table
CREATE TABLE interactions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    agent_id UUID REFERENCES agents(id),
    stimulus TEXT,
    reasoning TEXT,
    action TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Directory Structure
```
tinycontext/
├── __init__.py           # Main exports
├── agents/
│   ├── __init__.py
│   ├── base.py          # TinyPerson base class
│   ├── factory.py       # Agent factory
│   └── schemas/         # Protobuf definitions
├── reasoning/
│   ├── __init__.py
│   ├── react.py         # ReAct implementation
│   └── prompts.py       # Prompt templates
├── sessions/
│   ├── __init__.py
│   ├── manager.py       # Session orchestration
│   └── context.py       # Context management
├── utils/
│   ├── __init__.py
│   ├── llm.py          # LLM client abstraction
│   └── serialization.py # Save/load utilities
└── main.py              # CLI entry point
```

### Key Design Patterns
- **Factory Pattern** - For agent creation
- **Builder Pattern** - For complex prompt construction
- **Observer Pattern** - For session event handling
- **Strategy Pattern** - For different reasoning approaches

### Core Dependencies
- **openai** (>=1.0.0) - LLM integration
- **click** (>=8.1.0) - CLI framework
- **pydantic** (>=2.0.0) - Data validation
- **protobuf** (>=4.21.0) - Serialization
- **rich** (>=13.0.0) - Terminal UI
- **pyyaml** (>=6.0) - Configuration files
- **python-dotenv** (>=1.0.0) - Environment management
- **asyncpg** - Async PostgreSQL driver
- **pgvector** - Vector similarity search in PostgreSQL
- **sqlalchemy** (>=2.0.0) - ORM with pgvector support

### Testing Strategy
- Unit tests for each component
- Integration tests for agent interactions
- Mock LLM responses for deterministic testing
- Fixtures for common agent configurations

## Development Notes

- Python 3.11+ required for modern type hints
- Use type hints extensively for better IDE support
- Follow PEP 8 and use black/ruff for formatting
- Document all public APIs with docstrings
- Keep LLM calls abstracted for easy provider switching
- Implement proper error handling and logging
- Use dependency injection for testability

## Common Tasks

### Creating a New Agent Type
1. Extend TinyPerson base class
2. Override think_and_act method
3. Add specific prompts in prompts.py
4. Register in factory.py

### Adding a New CLI Command
1. Add command function in main.py
2. Use @click decorators for parameters
3. Implement command logic
4. Add help documentation

### Implementing a New Reasoning Pattern
1. Create new class in reasoning/
2. Implement reasoning interface
3. Add prompt templates
4. Integrate with TinyPerson

## Current Status

The project is in early development (v0.0.1). The README contains the vision and API design. Implementation should follow the patterns established in the README examples while maintaining clean, modular code.