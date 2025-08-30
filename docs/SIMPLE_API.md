# TinyContext Simple API

A simplified interface to TinyContext's powerful multi-agent orchestration capabilities, focusing on **context engineering** patterns and **12-factor agent principles**.

## 🚀 Quick Start

### Installation

```bash
# Install TinyContext
pip install -e .

# Or with OpenAI for simple mode
pip install openai
```

### Zero-Config Usage

```python
from tinycontext.simple import quick_start

# One-line setup
agent = quick_start()
result = await agent.run("Analyze this data", data={"sales": [100, 200, 300]})
print(result["output"])
```

### CLI Quick Start

```bash
# Setup environment
tinycontext setup

# Interactive demo
tinycontext demo

# Quick execution
tinycontext quick "Hello world!"

# With data
tinycontext quick "Analyze sales" --data '{"values": [1,2,3]}'
```

## 🧠 Context Engineering Patterns

TinyContext Simple implements the four core context engineering strategies:

### 1. Write Context - Persistent Memory

Save information outside the context window to survive truncation.

```python
from tinycontext.simple import ContextAgent

agent = ContextAgent()
await agent.initialize()

# Write persistent context
await agent.add_context(
    "customer_info", 
    "John Doe, premium customer since 2020, prefers email contact",
    tags=["customer", "preferences"],
    persistent=True
)

# Context survives across sessions
result = await agent.run("What do we know about this customer?")
```

### 2. Select Context - Relevant Retrieval  

Intelligently retrieve the most relevant information for current tasks.

```python
# Add multiple contexts with tags
await agent.add_context("product_info", "Our AI platform...", ["product"])
await agent.add_context("pricing_info", "Pricing starts at...", ["pricing"])
await agent.add_context("support_info", "Support available 24/7", ["support"])

# Context selection automatically retrieves relevant info
result = await agent.run(
    "How much does your product cost?",
    context_strategy="select"  # Automatically selects pricing_info
)
```

### 3. Compress Context - Smart Summarization

Compress long conversations while preserving essential information.

```python
# After a long conversation
result = await agent.run(
    "Summarize our entire conversation", 
    context_strategy="compress"  # Compresses history
)

# Get compressed history
history = await agent.get_conversation_history(compressed=True)
```

### 4. Isolate Context - Specialized Agents

Split context across specialized sub-agents to prevent confusion.

```python
# Create isolated contexts for different aspects
await agent.create_isolated_context("security_analysis", {
    "focus": {"type": str},
    "findings": {"type": list},
    "risk_level": {"type": str}
})

result = await agent.run(
    "Analyze security vulnerabilities in this code",
    context_strategy="isolate"  # Uses isolated context
)
```

## 🎯 Usage Examples

### Research Assistant

Demonstrates context selection and compression patterns.

```python
from tinycontext.simple import ContextAgent

# Initialize research assistant
assistant = ContextAgent(name="researcher", storage_path="./research_memory")
await assistant.initialize()

# Build knowledge base (Write Context)
await assistant.add_context(
    "ai_safety",
    "AI safety focuses on ensuring AI systems are beneficial and aligned with human values",
    tags=["ai", "safety", "research"]
)

# Research with context selection (Select Context)
result = await assistant.run(
    "What are the key challenges in AI safety?",
    context_strategy="select"
)

# Long research session (Compress Context)
for query in research_queries:
    result = await assistant.run(query, context_strategy="compress")
```

**Run the example:** `python examples/simple_research_assistant.py`

### Code Reviewer

Shows context isolation across different files and review aspects.

```python
from examples.simple_code_reviewer import CodeReviewSession

# Initialize review session
session = CodeReviewSession() 
await session.initialize()

# Add code files (Isolate Context per file)
await session.add_code_file("auth.py", code_content)
await session.add_code_file("api.py", code_content)

# Review with isolated contexts (different aspects)
security_review = await session.review_file("auth", ["security"])
performance_review = await session.review_file("api", ["performance"])

# Comprehensive review (Compress Context for large files)
final_report = await session.comprehensive_review(compress_large_files=True)
```

**Run the example:** `python examples/simple_code_reviewer.py`

### Customer Support

Demonstrates context persistence and handoffs.

```python
from examples.simple_customer_support import CustomerSupportSystem

# Initialize support system
support = CustomerSupportSystem()
await support.initialize()

# Create customer profile (Write Context)
await support.create_customer_profile("cust_123", "Alice", "alice@email.com")

# Handle support requests (Select Context for knowledge base)
ticket_id = await support.create_support_ticket("cust_123", "Login issues")
response = await support.handle_support_request(ticket_id, "Can't access my account")

# Escalate with context handoff (Isolate Context per specialist)
await support.escalate_ticket(ticket_id, "Security concern", "security_specialist")
```

**Run the example:** `python examples/simple_customer_support.py`

## 🔧 Configuration

### Environment Variables

```bash
# Preferred: Groq for high-speed inference (~500 tokens/sec)
GROQ_API_KEY=your-groq-api-key-here

# Fallback: OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Optional  
TINYCONTEXT_VERBOSE=false
ENABLE_OBSERVABILITY=false
TENSORZERO_MODEL=groq
TINYCONTEXT_STORAGE_PATH=./.tinycontext_memory
```

### Auto-Detection

TinyContext Simple automatically detects:

- ✅ OpenAI API key availability
- ✅ Full TinyContext framework vs simple mode
- ✅ TensorZero observability capabilities  
- ✅ Storage permissions and paths
- ✅ Dependencies and environment setup

```python
from tinycontext.simple import setup_environment

# Interactive environment check
status = setup_environment()
# Guides you through any missing setup
```

## 🎨 API Reference

### ContextAgent

Main agent class with automatic context engineering.

```python
class ContextAgent:
    def __init__(
        self,
        name: str = "context_agent",
        use_full_framework: bool = None,  # Auto-detected
        enable_observability: bool = None,  # Auto-detected  
        storage_path: str = None  # Auto-detected
    ):
        ...

    async def run(
        self,
        task: str,
        data: Optional[Dict] = None,
        context_strategy: str = "auto",  # "auto", "select", "compress", "isolate"
        max_iterations: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute task with automatic context engineering"""
        ...

    async def add_context(
        self, 
        key: str,
        content: str, 
        tags: Optional[List[str]] = None,
        persistent: bool = True
    ) -> None:
        """Add context for future task execution"""
        ...
```

### Context Engineering Components

#### ContextWriter - Write Context Pattern

```python
from tinycontext.simple import ContextWriter

writer = ContextWriter(storage_path="./memory")
memory_id = await writer.write_memory("key", "value", metadata={"type": "info"})
value = await writer.read_memory("key")
keys = await writer.list_memories()
```

#### ContextSelector - Select Context Pattern

```python
from tinycontext.simple import ContextSelector

selector = ContextSelector()
await selector.add_context("id", "content", tags=["tag1"], priority=2)
relevant = await selector.select_relevant(
    query="search term",
    max_contexts=3,
    tags_filter=["tag1"]
)
```

#### ContextCompressor - Compress Context Pattern

```python
from tinycontext.simple import ContextCompressor

compressor = ContextCompressor(compression_ratio=0.3)
compressed = await compressor.compress_conversation(messages, preserve_recent=3)
short_text = await compressor.compress_text(long_text, target_length=500)
```

#### ContextIsolator - Isolate Context Pattern

```python
from tinycontext.simple import ContextIsolator

isolator = ContextIsolator()
context_id = await isolator.create_isolated_context(
    "analysis", 
    {"result": {"type": str}, "confidence": {"type": float}}
)
await isolator.write_to_context(context_id, "result", "positive")
result = await isolator.read_from_context(context_id, "result")
```

## 🛠️ CLI Commands

### Setup and Configuration

```bash
# Interactive environment setup
tinycontext setup

# Initialize project structure  
tinycontext init

# List available examples
tinycontext examples
```

### Quick Execution

```bash
# Simple task
tinycontext quick "Hello world"

# With data and strategy
tinycontext quick "Analyze data" \
  --data '{"values": [1,2,3]}' \
  --strategy compress \
  --verbose

# Interactive demo mode
tinycontext demo
```

### Full Framework Commands  

```bash
# Run with full orchestration (if available)
tinycontext run "Complex multi-agent task" --verbose

# List agents
tinycontext agents

# Session management
tinycontext sessions
tinycontext replay session_id
```

## 🔄 Migration from Full Framework

TinyContext Simple preserves all advanced capabilities while providing simplified access.

### Simple API → Full Framework

```python
# Simple API
from tinycontext.simple import ContextAgent
agent = ContextAgent(use_full_framework=True)  # Enable full features

# Full Framework (when available)
from tinycontext.manager.async_context_manager import AsyncTinyContextManager
manager = AsyncTinyContextManager()
```

### Gradual Complexity

1. **Start Simple**: Use `quick_start()` for immediate results
2. **Add Context**: Use context engineering patterns as needed
3. **Enable Observability**: Set `ENABLE_OBSERVABILITY=true`
4. **Scale Up**: Migrate to full framework for production

## 🧪 Testing Your Setup

### Quick Test

```python
from tinycontext.simple import run_quick_task

# One-line test
result = await run_quick_task("Say hello!")
print(result)  # Should output a greeting
```

### CLI Test

```bash
# Environment check
tinycontext setup

# Quick execution test
tinycontext quick "What is 2+2?"

# Interactive test
tinycontext demo
```

### Example Scripts

```bash
# Research assistant demo
python examples/simple_research_assistant.py

# Code reviewer demo  
python examples/simple_code_reviewer.py

# Customer support demo
python examples/simple_customer_support.py
```

## 🚀 Next Steps

1. **Try the Examples**: Run the three example scripts to see context engineering in action
2. **Experiment with Strategies**: Test different context strategies (`auto`, `select`, `compress`, `isolate`)
3. **Build Your Use Case**: Adapt the patterns to your specific needs
4. **Scale Up**: When ready, explore the full TinyContext framework for advanced features

## 🤝 Contributing

TinyContext Simple is part of the larger TinyContext framework. See the main [README.md](../README.md) for contribution guidelines.

## 📚 Learn More

- [Context Engineering Research](https://rlancemartin.github.io/2025/06/23/context_engineering/) - Original research
- [12-Factor Agents](https://github.com/humanlayer/12-factor-agents) - Architectural principles  
- [Full TinyContext Documentation](../README.md) - Advanced features and capabilities