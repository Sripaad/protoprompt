"""
TinyFactory - Loads and manages TinyPerson agents from protobuf definitions.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Prompts:
    """Prompt configuration for an agent."""
    system: str = ""
    user: str = ""
    reasoning_template: str = ""
    action_template: str = ""


@dataclass
class TinyPerson:
    """
    TinyPerson agent definition.
    Note: This is a Python dataclass representation of the protobuf schema.
    In production, use compiled protobuf classes from person_pb2.py
    """
    name: str
    role: str
    persona: str = ""
    prompts: Prompts = field(default_factory=Prompts)
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    
    def __post_init__(self):
        """Convert dict prompts to Prompts object if needed."""
        if isinstance(self.prompts, dict):
            self.prompts = Prompts(**self.prompts)


class TinyFactory:
    """
    Factory for loading and managing TinyPerson agents.
    
    Supports loading from:
    - Protobuf files (when compiled)
    - YAML fallback
    - JSON fallback
    """
    
    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize the factory.
        
        Args:
            agents_dir: Directory containing agent definitions
        """
        self.agents_dir = agents_dir or Path("agents")
        self.registry: Dict[str, TinyPerson] = {}
        self._load_agents()
    
    def _load_agents(self) -> None:
        """Load all agents from the agents directory."""
        if not self.agents_dir.exists():
            self._load_default_agents()
            return
        
        # Try loading from YAML files
        for yaml_file in self.agents_dir.glob("*.yaml"):
            self._load_yaml_agent(yaml_file)
        
        # Try loading from JSON files
        for json_file in self.agents_dir.glob("*.json"):
            self._load_json_agent(json_file)
    
    def _load_yaml_agent(self, filepath: Path) -> None:
        """Load an agent from a YAML file."""
        try:
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                self._register_agent_from_dict(data)
        except Exception as e:
            print(f"Error loading agent from {filepath}: {e}")
    
    def _load_json_agent(self, filepath: Path) -> None:
        """Load an agent from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                self._register_agent_from_dict(data)
        except Exception as e:
            print(f"Error loading agent from {filepath}: {e}")
    
    def _register_agent_from_dict(self, data: Dict[str, Any]) -> None:
        """Register an agent from a dictionary."""
        prompts_data = data.get('prompts', {})
        prompts = Prompts(
            system=prompts_data.get('system', ''),
            user=prompts_data.get('user', ''),
            reasoning_template=prompts_data.get('reasoning_template', ''),
            action_template=prompts_data.get('action_template', '')
        )
        
        agent = TinyPerson(
            name=data['name'],
            role=data['role'],
            persona=data.get('persona', ''),
            prompts=prompts,
            metadata=data.get('metadata', {})
        )
        
        self.registry[agent.name] = agent
        self.registry[agent.role] = agent  # Also index by role
    
    def _load_default_agents(self) -> None:
        """Load default agents if no agents directory exists."""
        # Default strategist agent
        strategist = TinyPerson(
            name="strategist",
            role="strategist",
            persona="A strategic thinker who breaks down complex problems into manageable steps",
            prompts=Prompts(
                system="You are a strategic analyst. Break down problems into clear, actionable steps.",
                reasoning_template="Given the problem: {input}\nLet me analyze this step by step...",
                action_template="Based on my analysis, the next action should be: {action}"
            )
        )
        
        # Default planner agent
        planner = TinyPerson(
            name="planner",
            role="planner",
            persona="A methodical planner who creates detailed execution plans",
            prompts=Prompts(
                system="You are a project planner. Create detailed, executable plans.",
                reasoning_template="To accomplish: {input}\nI need to plan the following steps...",
                action_template="Here's the detailed plan: {plan}"
            )
        )
        
        # Default analyzer agent
        analyzer = TinyPerson(
            name="analyzer",
            role="analyzer",
            persona="An analytical thinker who examines data and patterns",
            prompts=Prompts(
                system="You are a data analyzer. Examine patterns and provide insights.",
                reasoning_template="Analyzing the data: {input}\nI observe the following patterns...",
                action_template="My analysis reveals: {insights}"
            )
        )
        
        self.registry["strategist"] = strategist
        self.registry["planner"] = planner
        self.registry["analyzer"] = analyzer
    
    def get_agent_by_role(self, role: str) -> Optional[TinyPerson]:
        """
        Get an agent by its role.
        
        Args:
            role: The role to search for
            
        Returns:
            TinyPerson if found, None otherwise
        """
        return self.registry.get(role)
    
    def get_agent_by_name(self, name: str) -> Optional[TinyPerson]:
        """
        Get an agent by its name.
        
        Args:
            name: The name to search for
            
        Returns:
            TinyPerson if found, None otherwise
        """
        return self.registry.get(name)
    
    def list_agents(self) -> List[TinyPerson]:
        """
        List all registered agents.
        
        Returns:
            List of TinyPerson agents
        """
        # Deduplicate (since we index by both name and role)
        seen = set()
        agents = []
        for agent in self.registry.values():
            if agent.name not in seen:
                seen.add(agent.name)
                agents.append(agent)
        return agents
    
    def register_agent(self, agent: TinyPerson) -> None:
        """
        Register a new agent.
        
        Args:
            agent: TinyPerson to register
        """
        self.registry[agent.name] = agent
        self.registry[agent.role] = agent