"""
Context Engineering Patterns

Implementation of the 4 core context engineering strategies:
1. Write Context - Persist information outside context window
2. Select Context - Retrieve relevant information for current task
3. Compress Context - Summarize long interaction trajectories
4. Isolate Context - Split context across specialized sub-agents
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import hashlib


class ContextWriter:
    """
    Write Context: Save information outside the context window
    
    Implements persistent memory that survives context truncation.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or ".tinycontext_memory")
        self.storage_path.mkdir(exist_ok=True)
        self.memory: Dict[str, Any] = {}
        
    async def write_memory(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        """Write information to persistent memory"""
        memory_id = hashlib.md5(f"{key}_{str(value)}".encode()).hexdigest()[:8]
        
        memory_entry = {
            "id": memory_id,
            "key": key,
            "value": value,
            "metadata": metadata or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store in memory
        self.memory[key] = memory_entry
        
        # Persist to disk
        file_path = self.storage_path / f"{key}.json"
        with open(file_path, 'w') as f:
            json.dump(memory_entry, f, indent=2)
            
        return memory_id
    
    async def read_memory(self, key: str) -> Optional[Any]:
        """Read from persistent memory"""
        if key in self.memory:
            return self.memory[key]["value"]
            
        # Try loading from disk
        file_path = self.storage_path / f"{key}.json"
        if file_path.exists():
            with open(file_path, 'r') as f:
                entry = json.load(f)
                self.memory[key] = entry
                return entry["value"]
                
        return None
    
    async def list_memories(self) -> List[str]:
        """List all memory keys"""
        disk_keys = [f.stem for f in self.storage_path.glob("*.json")]
        return list(set(list(self.memory.keys()) + disk_keys))


class ContextSelector:
    """
    Select Context: Retrieve relevant information for current tasks
    
    Uses semantic similarity and rule-based filtering to select
    the most relevant context for the current task.
    """
    
    def __init__(self):
        self.context_store: Dict[str, Dict] = {}
        self.embeddings_cache: Dict[str, List[float]] = {}
    
    async def add_context(self, 
                         context_id: str, 
                         content: str,
                         tags: Optional[List[str]] = None,
                         priority: int = 1) -> None:
        """Add context with metadata for selection"""
        self.context_store[context_id] = {
            "content": content,
            "tags": tags or [],
            "priority": priority,
            "length": len(content),
            "timestamp": asyncio.get_event_loop().time()
        }
    
    async def select_relevant(self, 
                            query: str,
                            max_contexts: int = 5,
                            max_tokens: int = 4000,
                            tags_filter: Optional[List[str]] = None) -> List[Dict]:
        """Select most relevant contexts for the query"""
        candidates = []
        
        for context_id, context_data in self.context_store.items():
            # Tag filtering
            if tags_filter:
                if not any(tag in context_data["tags"] for tag in tags_filter):
                    continue
            
            # Simple relevance scoring (in production, use embeddings)
            relevance_score = self._calculate_relevance(query, context_data["content"])
            
            candidates.append({
                "id": context_id,
                "content": context_data["content"],
                "score": relevance_score,
                "priority": context_data["priority"],
                "length": context_data["length"]
            })
        
        # Sort by relevance and priority
        candidates.sort(key=lambda x: (x["score"] * x["priority"]), reverse=True)
        
        # Select contexts within token limit
        selected = []
        total_tokens = 0
        
        for candidate in candidates[:max_contexts]:
            if total_tokens + candidate["length"] <= max_tokens:
                selected.append(candidate)
                total_tokens += candidate["length"]
            
        return selected
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Simple keyword-based relevance scoring"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
            
        intersection = query_words.intersection(content_words)
        return len(intersection) / len(query_words)


class ContextCompressor:
    """
    Compress Context: Summarize long interaction trajectories
    
    Implements hierarchical summarization to preserve essential
    information while reducing token usage.
    """
    
    def __init__(self, compression_ratio: float = 0.3):
        self.compression_ratio = compression_ratio
        self.summaries: Dict[str, str] = {}
    
    async def compress_conversation(self, 
                                  messages: List[Dict[str, str]],
                                  preserve_recent: int = 3) -> Dict[str, Any]:
        """Compress conversation history preserving recent messages"""
        if len(messages) <= preserve_recent:
            return {
                "compressed": False,
                "messages": messages,
                "summary": None
            }
        
        # Split into old and recent messages
        old_messages = messages[:-preserve_recent]
        recent_messages = messages[-preserve_recent:]
        
        # Create summary of old messages
        summary = await self._summarize_messages(old_messages)
        
        return {
            "compressed": True,
            "messages": recent_messages,
            "summary": summary,
            "original_count": len(messages),
            "compressed_count": preserve_recent + 1  # +1 for summary
        }
    
    async def compress_text(self, text: str, target_length: Optional[int] = None) -> str:
        """Compress text to target length while preserving key information"""
        if not target_length:
            target_length = int(len(text) * self.compression_ratio)
        
        if len(text) <= target_length:
            return text
        
        # Simple extractive summarization
        sentences = text.split('. ')
        if len(sentences) <= 1:
            return text[:target_length]
        
        # Keep most important sentences (first and last, plus some middle)
        important_indices = [0, len(sentences) - 1]
        if len(sentences) > 2:
            middle_count = max(1, target_length // 200)  # Rough sentences per 200 chars
            step = max(1, (len(sentences) - 2) // middle_count)
            important_indices.extend(range(1, len(sentences) - 1, step))
        
        important_indices = sorted(set(important_indices))
        compressed_sentences = [sentences[i] for i in important_indices[:target_length // 100]]
        
        return '. '.join(compressed_sentences)
    
    async def _summarize_messages(self, messages: List[Dict[str, str]]) -> str:
        """Create a summary of message history"""
        if not messages:
            return ""
        
        # Combine all content
        full_text = ""
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            full_text += f"{role}: {content}\n"
        
        # Simple summarization
        return await self.compress_text(full_text, target_length=300)


class ContextIsolator:
    """
    Isolate Context: Split context across specialized sub-agents
    
    Creates focused contexts for different aspects of a task,
    preventing context pollution and confusion.
    """
    
    def __init__(self):
        self.isolated_contexts: Dict[str, Dict] = {}
        self.context_schemas: Dict[str, Dict] = {}
    
    async def create_isolated_context(self, 
                                    context_id: str,
                                    schema: Dict[str, Any],
                                    initial_data: Optional[Dict] = None) -> str:
        """Create an isolated context with specific schema"""
        self.context_schemas[context_id] = schema
        self.isolated_contexts[context_id] = {
            "schema": schema,
            "data": initial_data or {},
            "history": [],
            "created_at": asyncio.get_event_loop().time()
        }
        return context_id
    
    async def write_to_context(self, 
                             context_id: str, 
                             key: str, 
                             value: Any,
                             validate: bool = True) -> bool:
        """Write data to isolated context with optional validation"""
        if context_id not in self.isolated_contexts:
            raise ValueError(f"Context {context_id} does not exist")
        
        context = self.isolated_contexts[context_id]
        
        # Schema validation
        if validate and key in context["schema"]:
            expected_type = context["schema"][key].get("type")
            if expected_type and not isinstance(value, expected_type):
                return False
        
        # Store data
        context["data"][key] = value
        context["history"].append({
            "action": "write",
            "key": key,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return True
    
    async def read_from_context(self, context_id: str, key: str) -> Any:
        """Read data from isolated context"""
        if context_id not in self.isolated_contexts:
            raise ValueError(f"Context {context_id} does not exist")
        
        context = self.isolated_contexts[context_id]
        return context["data"].get(key)
    
    async def get_context_summary(self, context_id: str) -> Dict[str, Any]:
        """Get summary of isolated context"""
        if context_id not in self.isolated_contexts:
            return {}
        
        context = self.isolated_contexts[context_id]
        return {
            "context_id": context_id,
            "data_keys": list(context["data"].keys()),
            "schema_keys": list(context["schema"].keys()),
            "history_length": len(context["history"]),
            "created_at": context["created_at"]
        }
    
    async def merge_contexts(self, 
                           source_contexts: List[str],
                           target_context: str,
                           merge_strategy: str = "latest") -> Dict[str, Any]:
        """Merge multiple isolated contexts"""
        merged_data = {}
        merge_history = []
        
        for context_id in source_contexts:
            if context_id not in self.isolated_contexts:
                continue
                
            source_context = self.isolated_contexts[context_id]
            
            for key, value in source_context["data"].items():
                if merge_strategy == "latest":
                    merged_data[key] = value
                elif merge_strategy == "first" and key not in merged_data:
                    merged_data[key] = value
                
                merge_history.append({
                    "source": context_id,
                    "key": key,
                    "strategy": merge_strategy
                })
        
        # Create merged context
        if target_context in self.isolated_contexts:
            self.isolated_contexts[target_context]["data"].update(merged_data)
        else:
            await self.create_isolated_context(target_context, {}, merged_data)
        
        return {
            "merged_keys": list(merged_data.keys()),
            "source_contexts": source_contexts,
            "target_context": target_context,
            "merge_history": merge_history
        }