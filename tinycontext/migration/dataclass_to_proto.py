"""
Migration utilities for converting between dataclass and protobuf representations.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import asyncio

from ..agents.loader import TinyPerson, Prompts, TinyFactory
from ..agents.proto_factory import ProtoFactory
from ..storage.agent_store import AgentStorage


class AgentMigrator:
    """
    Utilities for migrating agents between formats.
    
    Features:
    - Convert dataclass agents to proto format
    - Batch migration support
    - Validation tools
    - Rollback capability
    """
    
    def __init__(
        self,
        source_dir: str = "agents",
        target_dir: str = "agent_storage",
        backup_dir: str = "agent_backups"
    ):
        """
        Initialize migrator.
        
        Args:
            source_dir: Source directory for agents
            target_dir: Target storage directory
            backup_dir: Backup directory
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.backup_dir = Path(backup_dir)
        
        # Create directories
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.old_factory = TinyFactory(self.source_dir)
        self.new_factory = ProtoFactory(storage_path=str(self.target_dir))
        self.storage = AgentStorage(str(self.target_dir))
        
        # Migration tracking
        self.migration_log: List[Dict[str, Any]] = []
        self.rollback_data: Dict[str, Any] = {}
    
    async def migrate_agent(
        self,
        agent: TinyPerson,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Migrate a single agent to proto format.
        
        Args:
            agent: Agent to migrate
            validate: Whether to validate migration
            
        Returns:
            Migration result
        """
        result = {
            "agent_name": agent.name,
            "success": False,
            "storage_id": None,
            "errors": []
        }
        
        try:
            # Backup original
            backup_path = self.backup_dir / f"{agent.name}_backup.json"
            self._backup_agent(agent, backup_path)
            
            # Convert to enhanced format
            enhanced_agent = self._enhance_agent(agent)
            
            # Store in new format
            storage_id = await self.storage.store(enhanced_agent)
            result["storage_id"] = storage_id
            
            # Validate if requested
            if validate:
                validation_errors = await self._validate_migration(agent, storage_id)
                if validation_errors:
                    result["errors"] = validation_errors
                    # Rollback on validation failure
                    await self._rollback_agent(storage_id, backup_path)
                    return result
            
            result["success"] = True
            
            # Log migration
            self.migration_log.append({
                "agent_name": agent.name,
                "storage_id": storage_id,
                "backup_path": str(backup_path),
                "timestamp": json.dumps({"timestamp": "now"})
            })
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    async def migrate_all(
        self,
        validate: bool = True,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Migrate all agents.
        
        Args:
            validate: Whether to validate migrations
            parallel: Whether to migrate in parallel
            
        Returns:
            Migration summary
        """
        agents = self.old_factory.list_agents()
        
        if parallel:
            # Migrate in parallel
            tasks = [
                self.migrate_agent(agent, validate)
                for agent in agents
            ]
            results = await asyncio.gather(*tasks)
        else:
            # Migrate sequentially
            results = []
            for agent in agents:
                result = await self.migrate_agent(agent, validate)
                results.append(result)
        
        # Generate summary
        summary = {
            "total": len(agents),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
        
        # Save migration log
        log_path = self.backup_dir / "migration_log.json"
        with open(log_path, 'w') as f:
            json.dump({
                "summary": summary,
                "log": self.migration_log
            }, f, indent=2)
        
        return summary
    
    async def migrate_from_yaml(self, yaml_path: str) -> Dict[str, Any]:
        """
        Migrate an agent from YAML file.
        
        Args:
            yaml_path: Path to YAML file
            
        Returns:
            Migration result
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Create agent from YAML
        prompts = Prompts(
            system=data.get('prompts', {}).get('system', ''),
            user=data.get('prompts', {}).get('user', ''),
            reasoning_template=data.get('prompts', {}).get('reasoning_template', ''),
            action_template=data.get('prompts', {}).get('action_template', '')
        )
        
        agent = TinyPerson(
            name=data['name'],
            role=data['role'],
            persona=data.get('persona', ''),
            prompts=prompts,
            metadata=data.get('metadata', {})
        )
        
        # Migrate
        return await self.migrate_agent(agent)
    
    async def validate_all_migrations(self) -> List[Dict[str, Any]]:
        """
        Validate all completed migrations.
        
        Returns:
            List of validation results
        """
        validation_results = []
        
        for entry in self.migration_log:
            storage_id = entry["storage_id"]
            agent_name = entry["agent_name"]
            
            # Load original
            original = self.old_factory.get_agent_by_name(agent_name)
            if not original:
                validation_results.append({
                    "agent_name": agent_name,
                    "valid": False,
                    "errors": ["Original agent not found"]
                })
                continue
            
            # Validate
            errors = await self._validate_migration(original, storage_id)
            validation_results.append({
                "agent_name": agent_name,
                "valid": len(errors) == 0,
                "errors": errors
            })
        
        return validation_results
    
    async def rollback_migration(self, agent_name: str) -> bool:
        """
        Rollback a specific agent migration.
        
        Args:
            agent_name: Agent to rollback
            
        Returns:
            Success status
        """
        # Find migration entry
        entry = next(
            (e for e in self.migration_log if e["agent_name"] == agent_name),
            None
        )
        
        if not entry:
            return False
        
        storage_id = entry["storage_id"]
        backup_path = Path(entry["backup_path"])
        
        return await self._rollback_agent(storage_id, backup_path)
    
    async def rollback_all(self) -> Dict[str, Any]:
        """
        Rollback all migrations.
        
        Returns:
            Rollback summary
        """
        results = []
        
        for entry in self.migration_log:
            success = await self.rollback_migration(entry["agent_name"])
            results.append({
                "agent_name": entry["agent_name"],
                "success": success
            })
        
        return {
            "total": len(results),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "results": results
        }
    
    def _enhance_agent(self, agent: TinyPerson) -> TinyPerson:
        """
        Enhance a basic agent with additional fields.
        
        Args:
            agent: Basic agent
            
        Returns:
            Enhanced agent
        """
        # Add enhanced fields if not present
        if not hasattr(agent, 'capabilities'):
            agent.capabilities = []
        
        if not hasattr(agent, 'configuration'):
            agent.configuration = {}
        
        if not hasattr(agent, 'agent_id'):
            import uuid
            agent.agent_id = f"{agent.name}_{uuid.uuid4().hex[:8]}"
        
        # Infer capabilities from prompts
        if agent.prompts.system:
            system_lower = agent.prompts.system.lower()
            
            if "search" in system_lower or "research" in system_lower:
                agent.capabilities.append("search")
            if "analyze" in system_lower or "analysis" in system_lower:
                agent.capabilities.append("analyze")
            if "plan" in system_lower or "strategy" in system_lower:
                agent.capabilities.append("plan")
            if "code" in system_lower or "program" in system_lower:
                agent.capabilities.append("code")
        
        return agent
    
    def _backup_agent(self, agent: TinyPerson, backup_path: Path) -> None:
        """
        Backup an agent to file.
        
        Args:
            agent: Agent to backup
            backup_path: Backup file path
        """
        agent_dict = {
            "name": agent.name,
            "role": agent.role,
            "persona": agent.persona,
            "prompts": {
                "system": agent.prompts.system,
                "user": agent.prompts.user,
                "reasoning_template": agent.prompts.reasoning_template,
                "action_template": agent.prompts.action_template
            },
            "metadata": agent.metadata,
            "created_at": agent.created_at
        }
        
        with open(backup_path, 'w') as f:
            json.dump(agent_dict, f, indent=2)
    
    async def _validate_migration(
        self,
        original: TinyPerson,
        storage_id: str
    ) -> List[str]:
        """
        Validate a migration.
        
        Args:
            original: Original agent
            storage_id: Storage ID of migrated agent
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Load migrated agent
        migrated_data = await self.storage.retrieve(storage_id)
        if not migrated_data:
            errors.append("Failed to retrieve migrated agent")
            return errors
        
        # Validate core fields
        if migrated_data["name"] != original.name:
            errors.append(f"Name mismatch: {migrated_data['name']} != {original.name}")
        
        if migrated_data["role"] != original.role:
            errors.append(f"Role mismatch: {migrated_data['role']} != {original.role}")
        
        if migrated_data["persona"] != original.persona:
            errors.append(f"Persona mismatch")
        
        # Validate prompts
        original_prompts = original.prompts
        migrated_prompts = migrated_data["prompts"]
        
        if migrated_prompts["system"] != original_prompts.system:
            errors.append("System prompt mismatch")
        
        if migrated_prompts["user"] != original_prompts.user:
            errors.append("User prompt mismatch")
        
        if migrated_prompts["reasoning_template"] != original_prompts.reasoning_template:
            errors.append("Reasoning template mismatch")
        
        if migrated_prompts["action_template"] != original_prompts.action_template:
            errors.append("Action template mismatch")
        
        return errors
    
    async def _rollback_agent(
        self,
        storage_id: str,
        backup_path: Path
    ) -> bool:
        """
        Rollback a single agent.
        
        Args:
            storage_id: Storage ID to remove
            backup_path: Backup to restore from
            
        Returns:
            Success status
        """
        try:
            # Remove from storage (would implement delete method)
            # For now, just mark as rolled back
            self.rollback_data[storage_id] = str(backup_path)
            return True
        except Exception:
            return False
    
    def generate_migration_report(self) -> str:
        """
        Generate a migration report.
        
        Returns:
            Report as string
        """
        report = ["# Agent Migration Report\n"]
        report.append(f"Total migrations: {len(self.migration_log)}\n")
        
        if self.migration_log:
            report.append("\n## Migrated Agents\n")
            for entry in self.migration_log:
                report.append(f"- {entry['agent_name']} -> {entry['storage_id']}\n")
        
        if self.rollback_data:
            report.append("\n## Rolled Back\n")
            for storage_id, backup_path in self.rollback_data.items():
                report.append(f"- {storage_id} (backup: {backup_path})\n")
        
        return "".join(report)