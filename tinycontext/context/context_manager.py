"""
Context Manager - Manages shared context lifecycle and agent coordination.
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid

from .shared_context import SharedContext, Message, MessageType, AgentMemory
from ..agents.loader import TinyPerson
from ..storage.agent_store import AgentStorage


class ContextManager:
    """
    Manages shared contexts for agent collaboration.
    
    Features:
    - Context creation and lifecycle management
    - Agent assignment and coordination
    - Context persistence and recovery
    - Multi-context support
    """
    
    def __init__(self, storage_path: str = "context_storage"):
        """
        Initialize context manager.
        
        Args:
            storage_path: Base path for context storage
        """
        self.contexts: Dict[str, SharedContext] = {}
        self.agent_contexts: Dict[str, Set[str]] = {}  # agent_name -> set of context_ids
        self.storage = AgentStorage(storage_path)
        self.storage_path = storage_path
        
        # Active context tracking
        self.active_context_id: Optional[str] = None
        
        # Event handlers
        self._context_created_handlers = []
        self._context_destroyed_handlers = []
        self._agent_joined_handlers = []
        self._agent_left_handlers = []
    
    async def create_context(
        self,
        context_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        persist: bool = True
    ) -> SharedContext:
        """
        Create a new shared context.
        
        Args:
            context_id: Optional context ID
            episode_id: Optional TensorZero episode ID
            persist: Enable persistence
            
        Returns:
            Created context
        """
        context_id = context_id or f"ctx_{uuid.uuid4().hex[:8]}"
        
        # Create persistence path if enabled
        persist_path = None
        if persist:
            from pathlib import Path
            contexts_dir = Path(self.storage_path) / "contexts"
            contexts_dir.mkdir(parents=True, exist_ok=True)
            persist_path = str(contexts_dir / f"{context_id}.json")
        
        # Create context
        context = SharedContext(
            context_id=context_id,
            episode_id=episode_id,
            persist_enabled=persist,
            persist_path=persist_path
        )
        
        # Store context
        self.contexts[context_id] = context
        
        # Set as active if first context
        if not self.active_context_id:
            self.active_context_id = context_id
        
        # Notify handlers
        for handler in self._context_created_handlers:
            await handler(context_id)
        
        return context
    
    async def destroy_context(self, context_id: str) -> None:
        """
        Destroy a context and clean up resources.
        
        Args:
            context_id: Context to destroy
        """
        if context_id not in self.contexts:
            return
        
        # Remove all agents from context
        agents_in_context = [
            agent for agent, contexts in self.agent_contexts.items()
            if context_id in contexts
        ]
        
        for agent in agents_in_context:
            await self.remove_agent(context_id, agent)
        
        # Remove context
        del self.contexts[context_id]
        
        # Update active context
        if self.active_context_id == context_id:
            self.active_context_id = next(iter(self.contexts.keys()), None)
        
        # Notify handlers
        for handler in self._context_destroyed_handlers:
            await handler(context_id)
    
    async def get_context(self, context_id: Optional[str] = None) -> Optional[SharedContext]:
        """
        Get a context by ID or the active context.
        
        Args:
            context_id: Context ID or None for active
            
        Returns:
            Context or None
        """
        if context_id:
            return self.contexts.get(context_id)
        elif self.active_context_id:
            return self.contexts.get(self.active_context_id)
        return None
    
    async def assign_agent(
        self,
        agent: TinyPerson,
        context_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None
    ) -> bool:
        """
        Assign an agent to a context.
        
        Args:
            agent: Agent to assign
            context_id: Context ID or None for active
            capabilities: Agent capabilities
            
        Returns:
            Success status
        """
        context = await self.get_context(context_id)
        if not context:
            return False
        
        # Initialize agent memory in context
        if agent.name not in context.agent_memories:
            memory = AgentMemory(
                agent_name=agent.name,
                capabilities=capabilities or []
            )
            context.agent_memories[agent.name] = memory
        
        # Track agent-context association
        if agent.name not in self.agent_contexts:
            self.agent_contexts[agent.name] = set()
        self.agent_contexts[agent.name].add(context.context_id)
        
        # Send system message
        await context.broadcast(
            "system",
            f"Agent {agent.name} joined context",
            {"agent_role": agent.role}
        )
        
        # Store agent if not already stored
        await self.storage.store(agent)
        
        # Notify handlers
        for handler in self._agent_joined_handlers:
            await handler(context.context_id, agent.name)
        
        return True
    
    async def remove_agent(self, context_id: str, agent_name: str) -> bool:
        """
        Remove an agent from a context.
        
        Args:
            context_id: Context ID
            agent_name: Agent name
            
        Returns:
            Success status
        """
        context = self.contexts.get(context_id)
        if not context:
            return False
        
        # Send system message
        await context.broadcast(
            "system",
            f"Agent {agent_name} left context"
        )
        
        # Remove from tracking
        if agent_name in self.agent_contexts:
            self.agent_contexts[agent_name].discard(context_id)
            if not self.agent_contexts[agent_name]:
                del self.agent_contexts[agent_name]
        
        # Notify handlers
        for handler in self._agent_left_handlers:
            await handler(context_id, agent_name)
        
        return True
    
    async def broadcast_to_all(self, sender: str, message: str) -> None:
        """
        Broadcast a message to all active contexts.
        
        Args:
            sender: Sender name
            message: Message content
        """
        tasks = []
        for context in self.contexts.values():
            tasks.append(context.broadcast(sender, message))
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def get_agent_contexts(self, agent_name: str) -> List[str]:
        """
        Get all contexts an agent is in.
        
        Args:
            agent_name: Agent name
            
        Returns:
            List of context IDs
        """
        return list(self.agent_contexts.get(agent_name, set()))
    
    async def share_memory_across_contexts(
        self,
        agent_name: str,
        memory_key: str,
        memory_value: str
    ) -> None:
        """
        Share memory across all contexts an agent is in.
        
        Args:
            agent_name: Agent name
            memory_key: Memory key
            memory_value: Memory value
        """
        context_ids = await self.get_agent_contexts(agent_name)
        
        tasks = []
        for context_id in context_ids:
            context = self.contexts.get(context_id)
            if context:
                tasks.append(
                    context.update_agent_memory(agent_name, memory_key, memory_value)
                )
        
        if tasks:
            await asyncio.gather(*tasks)
    
    async def sync_agent_state(
        self,
        agent_name: str,
        state: Dict[str, Any]
    ) -> None:
        """
        Synchronize agent state across all contexts.
        
        Args:
            agent_name: Agent name
            state: State to sync
        """
        context_ids = await self.get_agent_contexts(agent_name)
        
        for context_id in context_ids:
            context = self.contexts.get(context_id)
            if context and agent_name in context.agent_memories:
                context.agent_memories[agent_name].state = state
    
    async def handoff_across_contexts(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        from_context_id: str,
        to_context_id: Optional[str] = None
    ) -> bool:
        """
        Hand off a task across contexts.
        
        Args:
            from_agent: Source agent
            to_agent: Target agent
            task: Task description
            from_context_id: Source context
            to_context_id: Target context (same if None)
            
        Returns:
            Success status
        """
        from_context = self.contexts.get(from_context_id)
        if not from_context:
            return False
        
        to_context_id = to_context_id or from_context_id
        to_context = self.contexts.get(to_context_id)
        if not to_context:
            return False
        
        # Get context from source
        from_memory = await from_context.get_agent_memory(from_agent)
        handoff_context = {
            "task": task,
            "from_agent": from_agent,
            "from_context": from_context_id,
            "state": from_memory.state if from_memory else {},
            "working_memory": from_memory.working_memory if from_memory else {}
        }
        
        # Perform handoff in source context
        await from_context.handoff(from_agent, to_agent, task, handoff_context)
        
        # If different context, also notify target context
        if from_context_id != to_context_id:
            await to_context.broadcast(
                "system",
                f"Task handed off from {from_agent} in context {from_context_id}",
                {"task": task, "from_context": from_context_id}
            )
            
            # Update target agent memory
            await to_context.update_agent_memory(
                to_agent,
                "handoff_task",
                task
            )
            await to_context.update_agent_memory(
                to_agent,
                "handoff_from",
                f"{from_agent}@{from_context_id}"
            )
        
        return True
    
    async def save_all_contexts(self) -> None:
        """Save all contexts to storage."""
        for context in self.contexts.values():
            if context.persist_enabled:
                await context._persist()
    
    async def load_context(self, context_id: str, path: str) -> SharedContext:
        """
        Load a context from storage.
        
        Args:
            context_id: Context ID
            path: Path to load from
            
        Returns:
            Loaded context
        """
        context = SharedContext(context_id=context_id)
        await context.load(path)
        
        self.contexts[context_id] = context
        
        # Set as active if first
        if not self.active_context_id:
            self.active_context_id = context_id
        
        return context
    
    def register_context_created_handler(self, handler) -> None:
        """Register handler for context creation."""
        self._context_created_handlers.append(handler)
    
    def register_context_destroyed_handler(self, handler) -> None:
        """Register handler for context destruction."""
        self._context_destroyed_handlers.append(handler)
    
    def register_agent_joined_handler(self, handler) -> None:
        """Register handler for agent joining."""
        self._agent_joined_handlers.append(handler)
    
    def register_agent_left_handler(self, handler) -> None:
        """Register handler for agent leaving."""
        self._agent_left_handlers.append(handler)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all contexts.
        
        Returns:
            Summary data
        """
        return {
            "context_count": len(self.contexts),
            "active_context": self.active_context_id,
            "contexts": [
                {
                    "id": ctx_id,
                    "agents": [
                        agent for agent, contexts in self.agent_contexts.items()
                        if ctx_id in contexts
                    ],
                    "message_count": len(ctx.messages),
                    "global_state_keys": list(ctx.global_state.keys())
                }
                for ctx_id, ctx in self.contexts.items()
            ],
            "total_agents": len(self.agent_contexts)
        }