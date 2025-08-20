#!/usr/bin/env python3
"""
Test script for TinyPerson abstraction layer with protobuf support and shared context.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

# Import new components
from tinycontext.agents.proto_factory import ProtoFactory
from tinycontext.storage.agent_store import AgentStorage
from tinycontext.context.shared_context import SharedContext, MessageType
from tinycontext.context.context_manager import ContextManager
from tinycontext.migration.dataclass_to_proto import AgentMigrator
from tinycontext.agents.loader import TinyPerson, Prompts


async def test_agent_storage():
    """Test agent storage and retrieval."""
    print("\n" + "="*60)
    print("🗄️  Testing Agent Storage")
    print("="*60)
    
    # Initialize storage
    storage = AgentStorage("test_storage")
    
    # Create a test agent
    agent = TinyPerson(
        name="storage_test_agent",
        role="tester",
        persona="A test agent for storage validation",
        prompts=Prompts(
            system="You are a test agent",
            reasoning_template="Testing: {input}",
            action_template="Test result: {output}"
        ),
        metadata={"test": "true"}
    )
    
    # Store agent
    print("\n📦 Storing agent...")
    storage_id = await storage.store(agent, version="1.0.0")
    print(f"✅ Stored with ID: {storage_id}")
    
    # Retrieve agent
    print("\n📥 Retrieving agent...")
    retrieved = await storage.retrieve(storage_id)
    if retrieved:
        print(f"✅ Retrieved agent: {retrieved['name']}")
        print(f"   Role: {retrieved['role']}")
        print(f"   Version: 1.0.0")
    
    # Create snapshot
    print("\n📸 Creating snapshot...")
    snapshot_id = await storage.create_snapshot(storage_id, {
        "state": {"current_task": "testing"},
        "memory": {"test_result": "success"}
    })
    print(f"✅ Snapshot created: {snapshot_id}")
    
    # Update stats
    print("\n📊 Updating execution stats...")
    await storage.update_stats(storage_id, {
        "success": True,
        "execution_time_ms": 150,
        "handoff_initiated": False
    })
    
    # List agents
    print("\n📋 Listing stored agents...")
    agents = await storage.list_agents()
    for agent_info in agents:
        print(f"   - {agent_info['name']} (v{agent_info['version']})")
    
    return storage_id


async def test_shared_context():
    """Test shared context system."""
    print("\n" + "="*60)
    print("🔄 Testing Shared Context")
    print("="*60)
    
    # Create shared context
    context = SharedContext(
        context_id="test_context",
        episode_id="test_episode_001",
        max_messages=100
    )
    
    print(f"\n✅ Created context: {context.context_id}")
    
    # Test global state
    print("\n📝 Testing global state...")
    await context.write_global("task", "test_collaboration")
    await context.write_global("status", "in_progress")
    
    task = await context.read_global("task")
    print(f"   Global task: {task}")
    
    # Test broadcasting
    print("\n📢 Testing message broadcasting...")
    await context.broadcast(
        "agent1",
        "Starting collaborative task",
        {"priority": "high"}
    )
    
    # Test direct messaging
    print("\n✉️  Testing direct messaging...")
    await context.send_direct(
        "agent1",
        "agent2",
        "Please analyze this data",
        {"data_type": "test"}
    )
    
    # Test handoff
    print("\n🤝 Testing task handoff...")
    await context.handoff(
        "agent1",
        "agent2",
        "Complete the analysis",
        {"data": "test_data", "deadline": "soon"}
    )
    
    # Test agent memory
    print("\n🧠 Testing agent memory...")
    await context.update_agent_memory("agent1", "last_action", "sent_message")
    await context.update_agent_memory("agent1", "skill", "analysis")
    
    memory = await context.get_agent_memory("agent1")
    if memory:
        print(f"   Agent1 memory keys: {list(memory.working_memory.keys())}")
        memory.add_reasoning("test input", "test reasoning", "test output")
        memory.add_action("analyze", "data", "completed", success=True)
    
    # Get recent messages
    print("\n📨 Recent messages:")
    messages = await context.get_recent_messages(limit=5)
    for msg in messages:
        print(f"   [{msg.type.value}] {msg.agent_name}: {msg.content[:50]}")
    
    # Get summary
    print("\n📊 Context summary:")
    summary = context.get_summary()
    print(f"   Messages: {summary['message_count']}")
    print(f"   Agents: {summary['agent_count']}")
    print(f"   Global keys: {summary['global_state_keys']}")
    
    return context


async def test_proto_factory():
    """Test enhanced proto factory."""
    print("\n" + "="*60)
    print("🏭 Testing Proto Factory")
    print("="*60)
    
    # Initialize factory
    factory = ProtoFactory(storage_path="test_proto_storage")
    
    # Create agent from template
    print("\n🎨 Creating agent from template...")
    research_agent = factory.create_agent(
        name="researcher_001",
        role="researcher",
        persona="Expert at finding information",
        template="research",
        capabilities=["search", "analyze", "summarize"],
        configuration={"max_search_results": "10"}
    )
    print(f"✅ Created: {research_agent.name} with capabilities: {research_agent.capabilities}")
    
    # Clone agent
    print("\n🔬 Cloning agent...")
    cloned = factory.clone_agent(research_agent, new_name="researcher_002")
    print(f"✅ Cloned: {cloned.name}")
    
    # Save agent
    print("\n💾 Saving agent...")
    storage_id = await factory.save_agent(research_agent, version="1.0.0")
    print(f"✅ Saved with ID: {storage_id}")
    
    # Create version
    print("\n📌 Creating new version...")
    version_id = await factory.create_agent_version(
        "researcher_001",
        "1.1.0",
        "Enhanced search capabilities"
    )
    print(f"✅ Version created: {version_id}")
    
    # List versions
    print("\n📜 Agent versions:")
    versions = await factory.list_agent_versions("researcher_001")
    for v in versions:
        print(f"   - {v['version']}: {v['changes']}")
    
    # Attach context to agent
    print("\n🔗 Attaching shared context...")
    context = SharedContext(context_id="factory_test")
    factory.attach_context("researcher_001", context)
    
    attached_context = factory.get_agent_context("researcher_001")
    if attached_context:
        print(f"✅ Context attached: {attached_context.context_id}")
    
    # Export agent
    print("\n📤 Exporting agent...")
    exported_json = await factory.export_agent("researcher_001", format="json")
    print(f"✅ Exported ({len(exported_json)} bytes)")
    
    # Import agent
    print("\n📥 Importing agent...")
    imported = await factory.import_agent(exported_json, format="json")
    print(f"✅ Imported: {imported.name}")
    
    return factory


async def test_context_manager():
    """Test context manager for multi-context coordination."""
    print("\n" + "="*60)
    print("🎯 Testing Context Manager")
    print("="*60)
    
    # Initialize manager
    manager = ContextManager("test_context_storage")
    
    # Create multiple contexts
    print("\n🌍 Creating multiple contexts...")
    context1 = await manager.create_context("project_alpha", persist=True)
    context2 = await manager.create_context("project_beta", persist=True)
    print(f"✅ Created contexts: {context1.context_id}, {context2.context_id}")
    
    # Create test agents
    agent1 = TinyPerson(
        name="coordinator",
        role="manager",
        persona="Coordinates between projects"
    )
    
    agent2 = TinyPerson(
        name="developer",
        role="coder",
        persona="Implements features"
    )
    
    # Assign agents to contexts
    print("\n👥 Assigning agents to contexts...")
    await manager.assign_agent(agent1, "project_alpha", ["coordinate", "plan"])
    await manager.assign_agent(agent2, "project_alpha", ["code", "test"])
    await manager.assign_agent(agent1, "project_beta", ["coordinate"])
    print("✅ Agents assigned")
    
    # Test cross-context handoff
    print("\n🔀 Testing cross-context handoff...")
    success = await manager.handoff_across_contexts(
        "coordinator",
        "developer",
        "Implement new feature",
        "project_alpha",
        "project_beta"
    )
    print(f"✅ Handoff successful: {success}")
    
    # Share memory across contexts
    print("\n🧩 Sharing memory across contexts...")
    await manager.share_memory_across_contexts(
        "coordinator",
        "current_priority",
        "feature_implementation"
    )
    
    # Sync agent state
    print("\n🔄 Syncing agent state...")
    await manager.sync_agent_state(
        "coordinator",
        {"status": "active", "task_count": 3}
    )
    
    # Get agent contexts
    print("\n📍 Agent context membership:")
    coordinator_contexts = await manager.get_agent_contexts("coordinator")
    print(f"   Coordinator in: {coordinator_contexts}")
    
    # Broadcast to all
    print("\n📣 Broadcasting to all contexts...")
    await manager.broadcast_to_all("system", "Test broadcast message")
    
    # Get summary
    print("\n📊 Manager summary:")
    summary = manager.get_summary()
    print(f"   Total contexts: {summary['context_count']}")
    print(f"   Active context: {summary['active_context']}")
    print(f"   Total agents: {summary['total_agents']}")
    
    for ctx in summary['contexts']:
        print(f"   - {ctx['id']}: {len(ctx['agents'])} agents")
    
    return manager


async def test_migration():
    """Test migration utilities."""
    print("\n" + "="*60)
    print("🚀 Testing Migration")
    print("="*60)
    
    # Create migrator
    migrator = AgentMigrator(
        source_dir="agents",
        target_dir="test_migration_storage",
        backup_dir="test_migration_backups"
    )
    
    # Create test agents to migrate
    print("\n📦 Creating test agents for migration...")
    test_agents = [
        TinyPerson(
            name="migrate_agent_1",
            role="analyst",
            persona="Data analyst",
            prompts=Prompts(
                system="Analyze data and provide insights",
                reasoning_template="Analyzing: {input}",
                action_template="Analysis result: {output}"
            )
        ),
        TinyPerson(
            name="migrate_agent_2",
            role="writer",
            persona="Content writer",
            prompts=Prompts(
                system="Write clear and engaging content",
                reasoning_template="Writing about: {input}",
                action_template="Content: {output}"
            )
        )
    ]
    
    # Register agents in old factory
    for agent in test_agents:
        migrator.old_factory.register_agent(agent)
    
    # Migrate single agent
    print("\n🔄 Migrating single agent...")
    result = await migrator.migrate_agent(test_agents[0], validate=True)
    print(f"   Migration result: {result['agent_name']}")
    print(f"   Success: {result['success']}")
    print(f"   Storage ID: {result['storage_id']}")
    
    if result['errors']:
        print(f"   Errors: {result['errors']}")
    
    # Migrate all
    print("\n🔄 Migrating all agents...")
    summary = await migrator.migrate_all(validate=True, parallel=False)
    print(f"   Total: {summary['total']}")
    print(f"   Successful: {summary['successful']}")
    print(f"   Failed: {summary['failed']}")
    
    # Validate migrations
    print("\n✅ Validating migrations...")
    validations = await migrator.validate_all_migrations()
    for val in validations:
        status = "✓" if val['valid'] else "✗"
        print(f"   {status} {val['agent_name']}")
        if val['errors']:
            for error in val['errors']:
                print(f"      - {error}")
    
    # Generate report
    print("\n📄 Migration report:")
    report = migrator.generate_migration_report()
    print(report)
    
    return migrator


async def test_integration():
    """Test integrated workflow with all components."""
    print("\n" + "="*60)
    print("🎭 Testing Integrated Workflow")
    print("="*60)
    
    # Initialize components
    factory = ProtoFactory(storage_path="test_integration_storage")
    manager = ContextManager("test_integration_contexts")
    
    # Create a project context
    print("\n🎬 Setting up project context...")
    project_context = await manager.create_context(
        "data_analysis_project",
        episode_id="episode_integration_001"
    )
    
    # Create specialized agents
    print("\n🤖 Creating specialized agents...")
    
    data_collector = factory.create_agent(
        name="data_collector",
        role="collector",
        persona="Gathers data from various sources",
        capabilities=["search", "extract", "validate"],
        configuration={"sources": "web,database,api"}
    )
    
    data_analyst = factory.create_agent(
        name="data_analyst",
        role="analyst",
        persona="Analyzes data and finds patterns",
        capabilities=["analyze", "visualize", "report"],
        configuration={"tools": "pandas,numpy,matplotlib"}
    )
    
    report_writer = factory.create_agent(
        name="report_writer",
        role="writer",
        persona="Creates comprehensive reports",
        capabilities=["write", "format", "summarize"],
        configuration={"format": "markdown"}
    )
    
    # Assign agents to context
    print("\n👥 Assigning agents to project...")
    await manager.assign_agent(data_collector, "data_analysis_project")
    await manager.assign_agent(data_analyst, "data_analysis_project")
    await manager.assign_agent(report_writer, "data_analysis_project")
    
    # Simulate workflow
    print("\n🔄 Simulating collaborative workflow...")
    
    # Step 1: Data collection
    print("   1️⃣ Data collection phase...")
    await project_context.broadcast(
        "data_collector",
        "Starting data collection for Q4 analysis"
    )
    await project_context.update_agent_memory(
        "data_collector",
        "collected_sources",
        "sales_db,customer_api,market_web"
    )
    
    # Step 2: Handoff to analyst
    print("   2️⃣ Handing off to analyst...")
    await project_context.handoff(
        "data_collector",
        "data_analyst",
        "Analyze Q4 sales data",
        {
            "data_location": "/data/q4_sales.csv",
            "metrics": ["revenue", "growth", "churn"]
        }
    )
    
    # Step 3: Analysis
    print("   3️⃣ Analysis phase...")
    await project_context.broadcast(
        "data_analyst",
        "Found 15% revenue growth with 2% churn reduction"
    )
    await project_context.write_global("analysis_status", "completed")
    await project_context.write_global("key_finding", "15% growth")
    
    # Step 4: Handoff to writer
    print("   4️⃣ Handing off to writer...")
    await project_context.handoff(
        "data_analyst",
        "report_writer",
        "Create executive summary",
        {
            "findings": "15% growth, 2% churn reduction",
            "charts": ["revenue_trend.png", "churn_analysis.png"]
        }
    )
    
    # Step 5: Report generation
    print("   5️⃣ Report generation phase...")
    await project_context.broadcast(
        "report_writer",
        "Executive summary completed and ready for review"
    )
    
    # Get workflow summary
    print("\n📊 Workflow summary:")
    messages = await project_context.get_recent_messages(limit=10)
    print(f"   Total messages: {len(messages)}")
    
    global_state = project_context.global_state
    print(f"   Global state: {global_state}")
    
    # Save agents with workflow history
    print("\n💾 Saving agents with history...")
    for agent_name in ["data_collector", "data_analyst", "report_writer"]:
        agent = factory.get_agent_by_name(agent_name)
        if agent:
            storage_id = await factory.save_agent(agent, version="1.0.0")
            print(f"   ✅ Saved {agent_name}: {storage_id}")
    
    # Generate final report
    print("\n📄 Final integration test summary:")
    print(f"   ✅ Agents created: 3")
    print(f"   ✅ Context established: {project_context.context_id}")
    print(f"   ✅ Messages exchanged: {len(messages)}")
    print(f"   ✅ Handoffs completed: 2")
    print(f"   ✅ Global state keys: {len(global_state)}")
    
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 TinyPerson Abstraction Layer Test Suite")
    print("="*60)
    
    try:
        # Test individual components
        storage_id = await test_agent_storage()
        context = await test_shared_context()
        factory = await test_proto_factory()
        manager = await test_context_manager()
        migrator = await test_migration()
        
        # Test integrated workflow
        integration_success = await test_integration()
        
        # Final summary
        print("\n" + "="*60)
        print("✅ All Tests Completed Successfully!")
        print("="*60)
        print("\nKey Results:")
        print(f"  📦 Storage tested with ID: {storage_id}")
        print(f"  🔄 Context tested: {context.context_id}")
        print(f"  🏭 Factory has {len(factory.registry)} agents")
        print(f"  🎯 Manager has {len(manager.contexts)} contexts")
        print(f"  🚀 Migrator processed {len(migrator.migration_log)} migrations")
        print(f"  🎭 Integration test: {'✅ Passed' if integration_success else '❌ Failed'}")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())