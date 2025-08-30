Context Engineering in TinyContext

Goals
- Make context assembly explicit, testable, and reusable across agents and workflows.

Core Building Blocks
- SharedContext: Global state, message bus, and per-agent memory.
- AgentMemory: Working memory per agent, with reasoning/action histories.
- Prompts: Role/system plus reasoning/action templates, parameterized by context.

Context Sources (examples)
- Task input and metadata (priority, owner, deadlines)
- File/system inputs (project READMEs, requirements)
- Prior messages and handoffs within the SharedContext
- External signals (retrieval results, metrics)

Assembly Pattern
1) Collect raw inputs → normalize shape (dict[str, Any])
2) Update SharedContext global_state and relevant AgentMemory entries
3) Build prompt variables from SharedContext: last N messages, key global_state fields, agent capabilities
4) Render reasoning/action templates using those variables

API Sketch
```
ctx = SharedContext(persist_enabled=True, persist_path="./sessions/ctx.json")
await ctx.write_global("task", task_text)
await ctx.update_agent_memory("researcher", "focus", "evaluate sources for credibility")

# Example: build prompt vars for an agent
mem = await ctx.get_agent_memory("researcher")
recent_msgs = await ctx.get_recent_messages(limit=5)
prompt_vars = {
  "input": task_text,
  "recent": [m.to_dict() for m in recent_msgs],
  "focus": mem.working_memory.get("focus", "")
}
```

Testing Context Assembly
- Unit test SharedContext operations (write_global/read, handoff updates)
- Snapshot expected prompt variables for given inputs

Extension Points
- Custom context providers: functions that enrich SharedContext from files/APIs
- Filters/transforms: choose what goes into prompts (windowing, summarization)
