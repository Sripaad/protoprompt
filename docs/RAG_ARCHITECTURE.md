# TinyContext RAG Architecture

## Overview

TinyContext implements Retrieval-Augmented Generation (RAG) as a multi-agent workflow where specialized TinyPerson agents collaborate within a TinyWorld FSM. This approach mirrors TensorZero's RAG example but leverages TinyContext's core philosophy: **everything is a TinyPerson agent**.

## Key Concepts

### 1. RAG as TinyPerson Agents

Instead of traditional "tools", RAG operations are performed by specialized TinyPerson agents:

- **Router Agent**: Analyzes queries and determines the approach
- **Searcher Agent**: Searches for relevant information
- **Loader Agent**: Extracts content from sources
- **Thinker Agent**: Reasons about gathered information
- **Answerer Agent**: Synthesizes final answers
- **Fact Checker Agent**: Verifies information accuracy

### 2. AsyncRAGWorld FSM

The RAG workflow is orchestrated through FSM state transitions:

```
IDLE → ROUTING → SEARCHING → LOADING → THINKING → VERIFYING → SYNTHESIZING → COMPLETE
         ↑                      ↓           ↓           ↓
         └──────────────────────────────────────────────┘
                    (Multi-hop reasoning loops)
```

### 3. Agent Handoffs

Complex queries are resolved through agent handoffs:
- Searcher hands off to Loader when content needs extraction
- Loader hands off to Thinker for reasoning
- Thinker may hand back to Searcher for more information
- Eventually hands off to Answerer for synthesis

## Architecture Components

### Core Modules

1. **`tinycontext/agents/rag_agents.py`**
   - Defines specialized RAG TinyPerson agents
   - RAGContext for maintaining search history
   - RAGAgentFactory for creating agent teams

2. **`tinycontext/core/rag_world.py`**
   - AsyncRAGWorld extends AsyncTinyWorld
   - RAG-specific states (SEARCHING, LOADING, etc.)
   - Message history and action tracking
   - Search/load/think/synthesize actions as state transitions

3. **`tinycontext/orchestration/rag_orchestrator.py`**
   - Coordinates multi-agent RAG workflows
   - Manages agent handoffs
   - Tracks execution metrics
   - Provides simple and research variants

## Implementation Patterns

### Simple RAG Flow
```python
# 1. Initialize RAG orchestrator with agents
orchestrator = RAGOrchestrator(llm_client)

# 2. Execute simple query
answer = await orchestrator.execute_simple_rag("What is async programming?")
```

### Multi-Hop RAG Flow
```python
# Complex query requiring multiple information gathering steps
result = await orchestrator.answer_query(
    "What dish is common in the hometown of the electron's discoverer?",
    max_iterations=10
)
```

### Custom RAG Workflows
```python
# Register custom action handlers
world.register_action_handler("wikipedia_search", custom_search)
world.register_action_handler("wikipedia_load", custom_loader)

# Execute with custom handlers
result = await orchestrator.answer_query(query)
```

## Key Differences from Traditional RAG

1. **No External Tools**: Actions are agent behaviors within FSM states
2. **Emergent Workflow**: RAG emerges from agent collaboration
3. **State-Driven**: All operations are FSM state transitions
4. **Full Observability**: Every action tracked through TensorZero
5. **Async Native**: Built for concurrent multi-agent execution

## TensorZero Integration

The system integrates with TensorZero for:
- LLM inference for each agent
- Observability of all agent actions
- Tracking of multi-hop reasoning paths
- Performance metrics and token usage

### Configuration

```toml
# tensorzero.toml
[functions.tiny_reasoning]
type = "chat"

[functions.tiny_search]
type = "chat"

[functions.rag_think]
type = "chat"

[functions.rag_synthesize]
type = "chat"
```

## Usage Examples

### Research Assistant
```python
# Create research-focused team
agents = RAGAgentFactory.create_research_team()

# Execute thorough research
result = await orchestrator.execute_research_rag(
    "Latest transformer architecture advances"
)
```

### Quick Q&A
```python
# Simple question answering
answer = await orchestrator.execute_simple_rag(
    "What is Python async/await?"
)
```

### Custom Wikipedia RAG
```python
# Similar to TensorZero's Wikipedia example
async def wikipedia_workflow(query):
    # Agents collaborate to search Wikipedia
    # Multi-hop through related articles
    # Synthesize comprehensive answer
    return await orchestrator.answer_query(query)
```

## Benefits of This Approach

1. **Composability**: Mix and match agents for different RAG strategies
2. **Interpretability**: Clear agent roles and state transitions
3. **Extensibility**: Easy to add new agent types or states
4. **Observability**: Full visibility into the reasoning process
5. **Reusability**: Agents can be reused across different workflows

## Future Enhancements

- Vector database integration for semantic search
- Streaming responses during synthesis
- Parallel agent execution for faster retrieval
- Caching layer for repeated queries
- Fine-tuned agents for specific domains

## Conclusion

TinyContext's RAG implementation demonstrates that complex information retrieval can emerge from simple agent interactions. By treating every operation as a TinyPerson agent action within an FSM, we achieve a clean, observable, and extensible RAG system that aligns with TinyContext's core philosophy.