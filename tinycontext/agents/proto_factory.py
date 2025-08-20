"""
Proto Factory - Enhanced agent factory with protobuf support.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

from .loader import TinyPerson, Prompts, TinyFactory
from ..storage.agent_store import AgentStorage
from ..context.shared_context import SharedContext, AgentMemory


class ProtoFactory(TinyFactory):
    """
    Enhanced factory for TinyPerson agents with protobuf support.
    
    Features:
    - Load/save agents in protobuf format
    - Convert between dataclass and proto representations
    - Agent templates and cloning
    - Hot reload support
    - Shared context integration
    """
    
    def __init__(
        self,
        agents_dir: Optional[Path] = None,
        storage_path: str = "agent_storage",
        enable_hot_reload: bool = False
    ):
        """
        Initialize proto factory.
        
        Args:
            agents_dir: Directory containing agent definitions
            storage_path: Path for agent storage
            enable_hot_reload: Enable hot reload of agents
        """
        super().__init__(agents_dir)
        
        self.storage = AgentStorage(storage_path)
        self.enable_hot_reload = enable_hot_reload
        
        # Agent templates
        self.templates: Dict[str, TinyPerson] = {}
        
        # Shared contexts for agents
        self.agent_contexts: Dict[str, SharedContext] = {}
        
        # Version tracking
        self.agent_versions: Dict[str, List[str]] = {}
        
        # Load templates
        self._load_templates()
        
        # Start hot reload if enabled
        if enable_hot_reload:
            self._start_hot_reload()
    
    def create_agent(
        self,
        name: str,
        role: str,
        persona: str = "",
        prompts: Optional[Dict[str, str]] = None,
        capabilities: Optional[List[str]] = None,
        configuration: Optional[Dict[str, str]] = None,
        template: Optional[str] = None
    ) -> TinyPerson:
        """
        Create a new agent with enhanced features.
        
        Args:
            name: Agent name
            role: Agent role
            persona: Agent personality
            prompts: Prompt configuration
            capabilities: Agent capabilities
            configuration: Agent configuration
            template: Optional template to use
            
        Returns:
            Created agent
        """
        # Use template if specified
        if template and template in self.templates:
            base_agent = self.clone_agent(self.templates[template])
            base_agent.name = name
            if role:
                base_agent.role = role
            if persona:
                base_agent.persona = persona
        else:
            # Create from scratch
            prompts_obj = Prompts()
            if prompts:
                prompts_obj.system = prompts.get('system', '')
                prompts_obj.user = prompts.get('user', '')
                prompts_obj.reasoning_template = prompts.get('reasoning_template', '')
                prompts_obj.action_template = prompts.get('action_template', '')
            
            base_agent = TinyPerson(
                name=name,
                role=role,
                persona=persona,
                prompts=prompts_obj,
                metadata={}
            )
        
        # Add enhanced fields
        base_agent.capabilities = capabilities or []
        base_agent.configuration = configuration or {}
        base_agent.agent_id = f"{name}_{uuid.uuid4().hex[:8]}"
        
        # Register agent
        self.register_agent(base_agent)
        
        return base_agent
    
    def clone_agent(self, agent: TinyPerson, new_name: Optional[str] = None) -> TinyPerson:
        """
        Clone an existing agent.
        
        Args:
            agent: Agent to clone
            new_name: Optional new name
            
        Returns:
            Cloned agent
        """
        # Create deep copy
        cloned = TinyPerson(
            name=new_name or f"{agent.name}_clone",
            role=agent.role,
            persona=agent.persona,
            prompts=Prompts(
                system=agent.prompts.system,
                user=agent.prompts.user,
                reasoning_template=agent.prompts.reasoning_template,
                action_template=agent.prompts.action_template
            ),
            metadata=dict(agent.metadata)
        )
        
        # Copy enhanced fields if they exist
        if hasattr(agent, 'capabilities'):
            cloned.capabilities = list(agent.capabilities)
        if hasattr(agent, 'configuration'):
            cloned.configuration = dict(agent.configuration)
        if hasattr(agent, 'agent_id'):
            cloned.agent_id = f"{cloned.name}_{uuid.uuid4().hex[:8]}"
        
        return cloned
    
    async def save_agent(self, agent: TinyPerson, version: Optional[str] = None) -> str:
        """
        Save an agent to storage.
        
        Args:
            agent: Agent to save
            version: Optional version string
            
        Returns:
            Storage ID
        """
        storage_id = await self.storage.store(agent, version)
        
        # Track version
        if agent.name not in self.agent_versions:
            self.agent_versions[agent.name] = []
        self.agent_versions[agent.name].append(storage_id)
        
        return storage_id
    
    async def load_agent(self, storage_id: str) -> Optional[TinyPerson]:
        """
        Load an agent from storage.
        
        Args:
            storage_id: Storage ID
            
        Returns:
            Loaded agent or None
        """
        agent_data = await self.storage.retrieve(storage_id)
        if not agent_data:
            return None
        
        # Convert to TinyPerson
        prompts = Prompts(
            system=agent_data["prompts"]["system"],
            user=agent_data["prompts"]["user"],
            reasoning_template=agent_data["prompts"]["reasoning_template"],
            action_template=agent_data["prompts"]["action_template"]
        )
        
        agent = TinyPerson(
            name=agent_data["name"],
            role=agent_data["role"],
            persona=agent_data["persona"],
            prompts=prompts,
            metadata=agent_data.get("metadata", {})
        )
        
        # Add enhanced fields
        agent.agent_id = agent_data.get("agent_id", f"{agent.name}_{uuid.uuid4().hex[:8]}")
        agent.capabilities = agent_data.get("capabilities", [])
        agent.configuration = agent_data.get("configuration", {})
        
        # Register loaded agent
        self.register_agent(agent)
        
        return agent
    
    async def list_stored_agents(self) -> List[Dict[str, Any]]:
        """
        List all stored agents.
        
        Returns:
            List of agent summaries
        """
        return await self.storage.list_agents()
    
    def attach_context(self, agent_name: str, context: SharedContext) -> None:
        """
        Attach a shared context to an agent.
        
        Args:
            agent_name: Agent name
            context: Shared context
        """
        self.agent_contexts[agent_name] = context
        
        # Initialize agent memory in context
        if agent_name not in context.agent_memories:
            agent = self.get_agent_by_name(agent_name)
            if agent:
                memory = AgentMemory(
                    agent_name=agent_name,
                    capabilities=getattr(agent, 'capabilities', [])
                )
                context.agent_memories[agent_name] = memory
    
    def get_agent_context(self, agent_name: str) -> Optional[SharedContext]:
        """
        Get the shared context for an agent.
        
        Args:
            agent_name: Agent name
            
        Returns:
            Shared context or None
        """
        return self.agent_contexts.get(agent_name)
    
    async def create_agent_version(
        self,
        agent_name: str,
        version: str,
        changes: str
    ) -> str:
        """
        Create a new version of an agent.
        
        Args:
            agent_name: Agent name
            version: Version string
            changes: Description of changes
            
        Returns:
            Version ID
        """
        agent = self.get_agent_by_name(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
        # Get latest storage ID
        if agent_name in self.agent_versions and self.agent_versions[agent_name]:
            storage_id = self.agent_versions[agent_name][-1]
        else:
            # Save agent first
            storage_id = await self.save_agent(agent)
        
        # Create version
        version_id = await self.storage.create_version(storage_id, version, changes)
        
        return version_id
    
    async def list_agent_versions(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        List all versions of an agent.
        
        Args:
            agent_name: Agent name
            
        Returns:
            List of versions
        """
        if agent_name not in self.agent_versions:
            return []
        
        versions = []
        for storage_id in self.agent_versions[agent_name]:
            agent_versions = await self.storage.list_versions(storage_id)
            versions.extend(agent_versions)
        
        return versions
    
    def _load_templates(self) -> None:
        """Load agent templates."""
        templates_dir = self.agents_dir / "templates" if self.agents_dir else Path("agents/templates")
        
        if not templates_dir.exists():
            # Create default templates
            self._create_default_templates()
            return
        
        # Load template files
        for template_file in templates_dir.glob("*.yaml"):
            try:
                with open(template_file, 'r') as f:
                    data = yaml.safe_load(f)
                    template_name = template_file.stem
                    
                    prompts = Prompts(
                        system=data.get('prompts', {}).get('system', ''),
                        user=data.get('prompts', {}).get('user', ''),
                        reasoning_template=data.get('prompts', {}).get('reasoning_template', ''),
                        action_template=data.get('prompts', {}).get('action_template', '')
                    )
                    
                    template = TinyPerson(
                        name=template_name,
                        role=data.get('role', template_name),
                        persona=data.get('persona', ''),
                        prompts=prompts,
                        metadata=data.get('metadata', {})
                    )
                    
                    # Add enhanced fields
                    template.capabilities = data.get('capabilities', [])
                    template.configuration = data.get('configuration', {})
                    
                    self.templates[template_name] = template
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")
    
    def _create_default_templates(self) -> None:
        """Create default agent templates."""
        # Research template
        research_template = TinyPerson(
            name="research_template",
            role="researcher",
            persona="A thorough researcher who gathers and analyzes information",
            prompts=Prompts(
                system="You are a research specialist. Gather comprehensive information and provide detailed analysis.",
                reasoning_template="Research query: {input}\nLet me gather and analyze relevant information...",
                action_template="Based on my research: {findings}"
            )
        )
        research_template.capabilities = ["search", "analyze", "summarize"]
        self.templates["research"] = research_template
        
        # Coding template
        coding_template = TinyPerson(
            name="coding_template",
            role="developer",
            persona="An expert programmer who writes clean, efficient code",
            prompts=Prompts(
                system="You are a software developer. Write clean, well-documented code.",
                reasoning_template="Programming task: {input}\nLet me design the solution...",
                action_template="Here's my implementation: {code}"
            )
        )
        coding_template.capabilities = ["code", "debug", "refactor"]
        self.templates["coding"] = coding_template
        
        # Manager template
        manager_template = TinyPerson(
            name="manager_template",
            role="manager",
            persona="A project manager who coordinates tasks and delegates work",
            prompts=Prompts(
                system="You are a project manager. Coordinate tasks and delegate to appropriate team members.",
                reasoning_template="Project requirement: {input}\nLet me plan the approach...",
                action_template="Task delegation: {plan}"
            )
        )
        manager_template.capabilities = ["plan", "delegate", "coordinate"]
        self.templates["manager"] = manager_template
    
    def _start_hot_reload(self) -> None:
        """Start hot reload monitoring."""
        # This would implement file watching for agent definitions
        # For now, it's a placeholder
        pass
    
    async def export_agent(self, agent_name: str, format: str = "json") -> str:
        """
        Export an agent in specified format.
        
        Args:
            agent_name: Agent name
            format: Export format (json, yaml, proto)
            
        Returns:
            Exported data as string
        """
        agent = self.get_agent_by_name(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} not found")
        
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
            "capabilities": getattr(agent, 'capabilities', []),
            "configuration": getattr(agent, 'configuration', {})
        }
        
        if format == "json":
            return json.dumps(agent_dict, indent=2)
        elif format == "yaml":
            return yaml.dump(agent_dict, default_flow_style=False)
        else:
            # For proto, would serialize to protobuf
            return json.dumps(agent_dict, indent=2)
    
    async def import_agent(self, data: str, format: str = "json") -> TinyPerson:
        """
        Import an agent from data.
        
        Args:
            data: Agent data
            format: Data format (json, yaml)
            
        Returns:
            Imported agent
        """
        if format == "json":
            agent_dict = json.loads(data)
        elif format == "yaml":
            agent_dict = yaml.safe_load(data)
        else:
            agent_dict = json.loads(data)
        
        agent = self.create_agent(
            name=agent_dict["name"],
            role=agent_dict["role"],
            persona=agent_dict.get("persona", ""),
            prompts=agent_dict.get("prompts"),
            capabilities=agent_dict.get("capabilities"),
            configuration=agent_dict.get("configuration")
        )
        
        return agent