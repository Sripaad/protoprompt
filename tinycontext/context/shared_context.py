"""
Shared Context System - Enables agent collaboration through shared state.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid


class MessageType(Enum):
    """Types of messages in the shared context."""
    BROADCAST = "broadcast"
    DIRECT = "direct"
    SYSTEM = "system"
    HANDOFF = "handoff"
    ERROR = "error"


@dataclass
class Message:
    """Message passed between agents."""
    agent_name: str
    content: str
    type: MessageType
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "content": self.content,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class AgentMemory:
    """Agent-specific memory storage."""
    agent_name: str
    working_memory: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    reasoning_history: List[Dict[str, Any]] = field(default_factory=list)
    action_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_reasoning(self, input_text: str, reasoning: str, output: str) -> None:
        """Add a reasoning step to history."""
        self.reasoning_history.append({
            "input": input_text,
            "reasoning": reasoning,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_action(self, action_type: str, action_data: str, result: str, success: bool = True) -> None:
        """Add an action to history."""
        self.action_history.append({
            "action_type": action_type,
            "action_data": action_data,
            "result": result,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })


class SharedContext:
    """
    Shared context for agent collaboration.
    
    Provides:
    - Global state sharing
    - Message passing between agents
    - Per-agent memory management
    - Context persistence
    """
    
    def __init__(
        self,
        context_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        max_messages: int = 1000,
        persist_enabled: bool = False,
        persist_path: Optional[str] = None
    ):
        """
        Initialize shared context.
        
        Args:
            context_id: Unique context identifier
            episode_id: TensorZero episode ID for tracking
            max_messages: Maximum message history size
            persist_enabled: Enable persistence
            persist_path: Path for persistence
        """
        self.context_id = context_id or f"ctx_{uuid.uuid4().hex[:8]}"
        self.episode_id = episode_id
        
        # Global state
        self.global_state: Dict[str, str] = {}
        
        # Message history
        self.messages: List[Message] = []
        self.max_messages = max_messages
        
        # Agent memories
        self.agent_memories: Dict[str, AgentMemory] = {}
        
        # Persistence
        self.persist_enabled = persist_enabled
        self.persist_path = persist_path
        
        # Timestamps
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Event handlers
        self._message_handlers: List[Callable] = []
        self._state_change_handlers: List[Callable] = []
        
        # Synchronization
        self._lock = asyncio.Lock()
    
    async def broadcast(self, agent_name: str, content: str, metadata: Optional[Dict[str, str]] = None) -> None:
        """
        Broadcast a message to all agents.
        
        Args:
            agent_name: Name of the broadcasting agent
            content: Message content
            metadata: Optional metadata
        """
        async with self._lock:
            message = Message(
                agent_name=agent_name,
                content=content,
                type=MessageType.BROADCAST,
                metadata=metadata or {}
            )
            
            await self._add_message(message)
            
            # Notify handlers
            for handler in self._message_handlers:
                await handler(message)
    
    async def send_direct(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Send a direct message to a specific agent.
        
        Args:
            from_agent: Sender agent name
            to_agent: Recipient agent name
            content: Message content
            metadata: Optional metadata
        """
        async with self._lock:
            message = Message(
                agent_name=from_agent,
                content=content,
                type=MessageType.DIRECT,
                metadata={**(metadata or {}), "to": to_agent}
            )
            
            await self._add_message(message)
            
            # Notify handlers
            for handler in self._message_handlers:
                await handler(message)
    
    async def handoff(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        context: Dict[str, Any]
    ) -> None:
        """
        Hand off a task from one agent to another.
        
        Args:
            from_agent: Agent handing off
            to_agent: Agent receiving
            task: Task description
            context: Task context
        """
        async with self._lock:
            message = Message(
                agent_name=from_agent,
                content=f"Handing off task to {to_agent}: {task}",
                type=MessageType.HANDOFF,
                metadata={
                    "to": to_agent,
                    "task": task,
                    "context": json.dumps(context)
                }
            )
            
            await self._add_message(message)
            
            # Update agent memories
            if from_agent in self.agent_memories:
                self.agent_memories[from_agent].add_action(
                    "handoff",
                    f"to:{to_agent}",
                    f"task:{task}",
                    success=True
                )
            
            if to_agent not in self.agent_memories:
                self.agent_memories[to_agent] = AgentMemory(agent_name=to_agent)
            
            self.agent_memories[to_agent].working_memory["handoff_task"] = task
            self.agent_memories[to_agent].working_memory["handoff_context"] = json.dumps(context)
            
            # Notify handlers
            for handler in self._message_handlers:
                await handler(message)
    
    async def read_global(self, key: str) -> Optional[str]:
        """
        Read from global state.
        
        Args:
            key: State key
            
        Returns:
            Value or None if not found
        """
        async with self._lock:
            return self.global_state.get(key)
    
    async def write_global(self, key: str, value: str) -> None:
        """
        Write to global state.
        
        Args:
            key: State key
            value: State value
        """
        async with self._lock:
            old_value = self.global_state.get(key)
            self.global_state[key] = value
            self.updated_at = datetime.now()
            
            # Notify state change handlers
            for handler in self._state_change_handlers:
                await handler(key, old_value, value)
            
            # Persist if enabled
            if self.persist_enabled:
                await self._persist()
    
    async def update_agent_memory(
        self,
        agent_name: str,
        memory_key: str,
        memory_value: str
    ) -> None:
        """
        Update an agent's working memory.
        
        Args:
            agent_name: Agent name
            memory_key: Memory key
            memory_value: Memory value
        """
        async with self._lock:
            if agent_name not in self.agent_memories:
                self.agent_memories[agent_name] = AgentMemory(agent_name=agent_name)
            
            self.agent_memories[agent_name].working_memory[memory_key] = memory_value
            self.updated_at = datetime.now()
    
    async def get_agent_memory(self, agent_name: str) -> Optional[AgentMemory]:
        """
        Get an agent's memory.
        
        Args:
            agent_name: Agent name
            
        Returns:
            Agent memory or None
        """
        async with self._lock:
            return self.agent_memories.get(agent_name)
    
    async def get_recent_messages(
        self,
        limit: int = 10,
        agent_filter: Optional[str] = None,
        type_filter: Optional[MessageType] = None
    ) -> List[Message]:
        """
        Get recent messages with optional filtering.
        
        Args:
            limit: Maximum number of messages
            agent_filter: Filter by agent name
            type_filter: Filter by message type
            
        Returns:
            List of messages
        """
        async with self._lock:
            messages = self.messages[-limit:]
            
            if agent_filter:
                messages = [m for m in messages if m.agent_name == agent_filter]
            
            if type_filter:
                messages = [m for m in messages if m.type == type_filter]
            
            return messages
    
    async def clear_messages(self) -> None:
        """Clear message history."""
        async with self._lock:
            self.messages.clear()
            self.updated_at = datetime.now()
    
    def register_message_handler(self, handler: Callable) -> None:
        """
        Register a message handler.
        
        Args:
            handler: Async function to handle messages
        """
        self._message_handlers.append(handler)
    
    def register_state_change_handler(self, handler: Callable) -> None:
        """
        Register a state change handler.
        
        Args:
            handler: Async function to handle state changes
        """
        self._state_change_handlers.append(handler)
    
    async def _add_message(self, message: Message) -> None:
        """Add a message to history with overflow management."""
        self.messages.append(message)
        
        # Trim if exceeds max
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
        
        self.updated_at = datetime.now()
        
        # Persist if enabled
        if self.persist_enabled:
            await self._persist()
    
    async def _persist(self) -> None:
        """Persist context to storage."""
        if not self.persist_path:
            return
        
        # Create persistence data
        data = {
            "context_id": self.context_id,
            "episode_id": self.episode_id,
            "global_state": self.global_state,
            "messages": [m.to_dict() for m in self.messages],
            "agent_memories": {
                name: {
                    "working_memory": mem.working_memory,
                    "capabilities": mem.capabilities,
                    "state": mem.state,
                    "reasoning_history": mem.reasoning_history[-10:],  # Keep last 10
                    "action_history": mem.action_history[-10:]  # Keep last 10
                }
                for name, mem in self.agent_memories.items()
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        # Save to file
        import aiofiles
        async with aiofiles.open(self.persist_path, 'w') as f:
            await f.write(json.dumps(data, indent=2))
    
    async def load(self, path: str) -> None:
        """
        Load context from persistence.
        
        Args:
            path: Path to load from
        """
        import aiofiles
        async with aiofiles.open(path, 'r') as f:
            data = json.loads(await f.read())
        
        self.context_id = data["context_id"]
        self.episode_id = data.get("episode_id")
        self.global_state = data["global_state"]
        
        # Restore messages
        self.messages = []
        for msg_data in data["messages"]:
            self.messages.append(Message(
                agent_name=msg_data["agent_name"],
                content=msg_data["content"],
                type=MessageType(msg_data["type"]),
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {})
            ))
        
        # Restore agent memories
        self.agent_memories = {}
        for name, mem_data in data.get("agent_memories", {}).items():
            memory = AgentMemory(agent_name=name)
            memory.working_memory = mem_data["working_memory"]
            memory.capabilities = mem_data["capabilities"]
            memory.state = mem_data["state"]
            memory.reasoning_history = mem_data.get("reasoning_history", [])
            memory.action_history = mem_data.get("action_history", [])
            self.agent_memories[name] = memory
        
        self.created_at = datetime.fromisoformat(data["created_at"])
        self.updated_at = datetime.fromisoformat(data["updated_at"])
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the context state.
        
        Returns:
            Context summary
        """
        return {
            "context_id": self.context_id,
            "episode_id": self.episode_id,
            "message_count": len(self.messages),
            "agent_count": len(self.agent_memories),
            "global_state_keys": list(self.global_state.keys()),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "agents": list(self.agent_memories.keys())
        }