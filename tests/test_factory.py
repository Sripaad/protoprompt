"""
Tests for TinyFactory agent loader.
"""
from tinycontext.agents.loader import TinyFactory, TinyPerson, Prompts


def test_factory_initialization():
    """Test factory initializes with default agents."""
    factory = TinyFactory()
    
    # Should have default agents
    agents = factory.list_agents()
    assert len(agents) > 0
    
    # Check default roles exist
    assert factory.get_agent_by_role("strategist") is not None
    assert factory.get_agent_by_role("planner") is not None
    assert factory.get_agent_by_role("analyzer") is not None


def test_get_agent_by_role():
    """Test retrieving agents by role."""
    factory = TinyFactory()
    
    agent = factory.get_agent_by_role("strategist")
    assert agent is not None
    assert agent.role == "strategist"
    assert agent.name == "strategist"


def test_get_agent_by_name():
    """Test retrieving agents by name."""
    factory = TinyFactory()
    
    agent = factory.get_agent_by_name("planner")
    assert agent is not None
    assert agent.name == "planner"


def test_register_custom_agent():
    """Test registering a custom agent."""
    factory = TinyFactory()
    
    custom_agent = TinyPerson(
        name="custom_agent",
        role="custom_role",
        persona="A custom test agent",
        prompts=Prompts(
            system="Custom system prompt",
            reasoning_template="Custom reasoning: {input}"
        )
    )
    
    factory.register_agent(custom_agent)
    
    # Should be retrievable by both name and role
    assert factory.get_agent_by_name("custom_agent") is not None
    assert factory.get_agent_by_role("custom_role") is not None


def test_list_agents_deduplication():
    """Test that list_agents deduplicates agents."""
    factory = TinyFactory()
    
    # Agents are indexed by both name and role
    # list_agents should deduplicate
    agents = factory.list_agents()
    agent_names = [a.name for a in agents]
    
    # Check no duplicates
    assert len(agent_names) == len(set(agent_names))


def test_agent_attributes():
    """Test agent attributes are properly set."""
    factory = TinyFactory()
    agent = factory.get_agent_by_role("strategist")
    
    assert agent.name == "strategist"
    assert agent.role == "strategist"
    assert agent.persona != ""
    assert agent.prompts.system != ""
    assert agent.created_at > 0


def test_prompts_structure():
    """Test Prompts dataclass structure."""
    prompts = Prompts(
        system="System prompt",
        user="User prompt",
        reasoning_template="Reasoning: {input}",
        action_template="Action: {action}"
    )
    
    assert prompts.system == "System prompt"
    assert prompts.user == "User prompt"
    assert prompts.reasoning_template == "Reasoning: {input}"
    assert prompts.action_template == "Action: {action}"


def test_default_prompts():
    """Test default prompts are empty strings."""
    prompts = Prompts()
    
    assert prompts.system == ""
    assert prompts.user == ""
    assert prompts.reasoning_template == ""
    assert prompts.action_template == ""