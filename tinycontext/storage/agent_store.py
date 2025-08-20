"""
Agent Storage Layer - Proto-based persistence for TinyPerson agents.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

# For now, we'll use JSON for storage until protobuf compilation is set up
# In production, this would use the compiled protobuf classes

class AgentStorage:
    """
    Persistent storage for TinyPerson agents using protobuf serialization.
    
    Features:
    - Save/load agents with versioning
    - Snapshot management
    - Execution statistics tracking
    - Bulk operations
    """
    
    def __init__(self, storage_path: str = "agent_storage"):
        """
        Initialize agent storage.
        
        Args:
            storage_path: Base path for agent storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.agents_dir = self.storage_path / "agents"
        self.snapshots_dir = self.storage_path / "snapshots"
        self.versions_dir = self.storage_path / "versions"
        
        for dir_path in [self.agents_dir, self.snapshots_dir, self.versions_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # In-memory cache
        self._cache: Dict[str, Any] = {}
        self._stats: Dict[str, Dict[str, Any]] = {}
    
    async def store(self, agent: Any, version: Optional[str] = None) -> str:
        """
        Store an agent with optional versioning.
        
        Args:
            agent: TinyPerson agent to store
            version: Optional version string
            
        Returns:
            Storage ID for the agent
        """
        # Generate storage ID
        storage_id = f"{agent.name}_{uuid.uuid4().hex[:8]}"
        
        # Create storage record
        storage_record = {
            "agent": {
                "name": agent.name,
                "role": agent.role,
                "persona": agent.persona,
                "prompts": {
                    "system": agent.prompts.system if hasattr(agent.prompts, 'system') else "",
                    "user": agent.prompts.user if hasattr(agent.prompts, 'user') else "",
                    "reasoning_template": agent.prompts.reasoning_template if hasattr(agent.prompts, 'reasoning_template') else "",
                    "action_template": agent.prompts.action_template if hasattr(agent.prompts, 'action_template') else ""
                },
                "metadata": agent.metadata if hasattr(agent, 'metadata') else {},
                "created_at": agent.created_at if hasattr(agent, 'created_at') else int(datetime.now().timestamp()),
                "agent_id": storage_id,
                "capabilities": getattr(agent, 'capabilities', []),
                "configuration": getattr(agent, 'configuration', {})
            },
            "metadata": {
                "storage_id": storage_id,
                "storage_path": str(self.agents_dir / f"{storage_id}.json"),
                "stored_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 0,
                "tags": {}
            },
            "version": {
                "version_id": version or "1.0.0",
                "major": 1,
                "minor": 0,
                "patch": 0,
                "parent_version": "",
                "created_at": datetime.now().isoformat(),
                "change_description": "Initial version"
            }
        }
        
        # Save to file
        file_path = self.agents_dir / f"{storage_id}.json"
        with open(file_path, 'w') as f:
            json.dump(storage_record, f, indent=2)
        
        # Update cache
        self._cache[storage_id] = storage_record
        
        # Initialize stats
        self._stats[storage_id] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "handoffs_initiated": 0,
            "handoffs_received": 0,
            "average_execution_time_ms": 0.0,
            "last_execution": None
        }
        
        return storage_id
    
    async def retrieve(self, storage_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an agent by storage ID.
        
        Args:
            storage_id: Storage ID of the agent
            
        Returns:
            Agent data or None if not found
        """
        # Check cache first
        if storage_id in self._cache:
            record = self._cache[storage_id]
            # Update access metadata
            record["metadata"]["last_accessed"] = datetime.now().isoformat()
            record["metadata"]["access_count"] += 1
            return record["agent"]
        
        # Load from file
        file_path = self.agents_dir / f"{storage_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            record = json.load(f)
        
        # Update cache
        self._cache[storage_id] = record
        
        # Update access metadata
        record["metadata"]["last_accessed"] = datetime.now().isoformat()
        record["metadata"]["access_count"] += 1
        
        # Save updated metadata
        with open(file_path, 'w') as f:
            json.dump(record, f, indent=2)
        
        return record["agent"]
    
    async def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all stored agents.
        
        Returns:
            List of agent summaries
        """
        agents = []
        
        for file_path in self.agents_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                record = json.load(f)
                agents.append({
                    "storage_id": record["metadata"]["storage_id"],
                    "name": record["agent"]["name"],
                    "role": record["agent"]["role"],
                    "version": record["version"]["version_id"],
                    "stored_at": record["metadata"]["stored_at"],
                    "access_count": record["metadata"]["access_count"]
                })
        
        return agents
    
    async def create_snapshot(self, storage_id: str, state: Dict[str, Any]) -> str:
        """
        Create a snapshot of an agent's current state.
        
        Args:
            storage_id: Storage ID of the agent
            state: Current state to snapshot
            
        Returns:
            Snapshot ID
        """
        snapshot_id = f"snapshot_{storage_id}_{uuid.uuid4().hex[:8]}"
        
        snapshot = {
            "snapshot_id": snapshot_id,
            "storage_id": storage_id,
            "state": state.get("state", {}),
            "memory": state.get("memory", {}),
            "stats": self._stats.get(storage_id, {}),
            "created_at": datetime.now().isoformat()
        }
        
        # Save snapshot
        file_path = self.snapshots_dir / f"{snapshot_id}.json"
        with open(file_path, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        return snapshot_id
    
    async def restore_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore an agent from a snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to restore
            
        Returns:
            Snapshot data or None if not found
        """
        file_path = self.snapshots_dir / f"{snapshot_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, 'r') as f:
            snapshot = json.load(f)
        
        return snapshot
    
    async def update_stats(self, storage_id: str, execution_result: Dict[str, Any]) -> None:
        """
        Update execution statistics for an agent.
        
        Args:
            storage_id: Storage ID of the agent
            execution_result: Execution result data
        """
        if storage_id not in self._stats:
            self._stats[storage_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "handoffs_initiated": 0,
                "handoffs_received": 0,
                "average_execution_time_ms": 0.0,
                "last_execution": None
            }
        
        stats = self._stats[storage_id]
        stats["total_executions"] += 1
        
        if execution_result.get("success", False):
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        if execution_result.get("handoff_initiated", False):
            stats["handoffs_initiated"] += 1
        
        if execution_result.get("handoff_received", False):
            stats["handoffs_received"] += 1
        
        # Update average execution time
        execution_time = execution_result.get("execution_time_ms", 0)
        current_avg = stats["average_execution_time_ms"]
        total_execs = stats["total_executions"]
        stats["average_execution_time_ms"] = (
            (current_avg * (total_execs - 1) + execution_time) / total_execs
        )
        
        stats["last_execution"] = datetime.now().isoformat()
    
    async def create_version(self, storage_id: str, version: str, changes: str) -> str:
        """
        Create a new version of an agent.
        
        Args:
            storage_id: Storage ID of the agent
            version: Version string (e.g., "1.1.0")
            changes: Description of changes
            
        Returns:
            Version ID
        """
        # Load current agent
        agent_data = await self.retrieve(storage_id)
        if not agent_data:
            raise ValueError(f"Agent {storage_id} not found")
        
        # Create version record
        version_id = f"v_{storage_id}_{version.replace('.', '_')}"
        
        version_record = {
            "version_id": version_id,
            "storage_id": storage_id,
            "version": version,
            "agent_data": agent_data,
            "changes": changes,
            "created_at": datetime.now().isoformat()
        }
        
        # Save version
        file_path = self.versions_dir / f"{version_id}.json"
        with open(file_path, 'w') as f:
            json.dump(version_record, f, indent=2)
        
        return version_id
    
    async def list_versions(self, storage_id: str) -> List[Dict[str, Any]]:
        """
        List all versions of an agent.
        
        Args:
            storage_id: Storage ID of the agent
            
        Returns:
            List of version summaries
        """
        versions = []
        
        for file_path in self.versions_dir.glob(f"v_{storage_id}_*.json"):
            with open(file_path, 'r') as f:
                record = json.load(f)
                versions.append({
                    "version_id": record["version_id"],
                    "version": record["version"],
                    "changes": record["changes"],
                    "created_at": record["created_at"]
                })
        
        return sorted(versions, key=lambda x: x["created_at"], reverse=True)
    
    async def export_collection(self, agent_ids: List[str], collection_name: str) -> str:
        """
        Export multiple agents as a collection.
        
        Args:
            agent_ids: List of storage IDs to export
            collection_name: Name for the collection
            
        Returns:
            Collection file path
        """
        collection_id = f"collection_{uuid.uuid4().hex[:8]}"
        
        agents = []
        for agent_id in agent_ids:
            agent_data = await self.retrieve(agent_id)
            if agent_data:
                agents.append(agent_data)
        
        collection = {
            "collection_id": collection_id,
            "collection_name": collection_name,
            "agents": agents,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "agent_count": len(agents)
            }
        }
        
        # Save collection
        file_path = self.storage_path / f"{collection_name}.collection.json"
        with open(file_path, 'w') as f:
            json.dump(collection, f, indent=2)
        
        return str(file_path)
    
    async def import_collection(self, file_path: str) -> List[str]:
        """
        Import agents from a collection file.
        
        Args:
            file_path: Path to collection file
            
        Returns:
            List of imported storage IDs
        """
        with open(file_path, 'r') as f:
            collection = json.load(f)
        
        imported_ids = []
        for agent_data in collection["agents"]:
            # Create a simple agent object for storage
            class SimpleAgent:
                def __init__(self, data):
                    self.name = data["name"]
                    self.role = data["role"]
                    self.persona = data.get("persona", "")
                    self.prompts = type('obj', (object,), data.get("prompts", {}))
                    self.metadata = data.get("metadata", {})
                    self.created_at = data.get("created_at", int(datetime.now().timestamp()))
                    self.capabilities = data.get("capabilities", [])
                    self.configuration = data.get("configuration", {})
            
            agent = SimpleAgent(agent_data)
            storage_id = await self.store(agent)
            imported_ids.append(storage_id)
        
        return imported_ids