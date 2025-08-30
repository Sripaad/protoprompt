#!/usr/bin/env python3
"""
Customer Support Example - Context Persistence & Handoffs Showcase

This example demonstrates context engineering patterns for customer support:
1. Write Context - Persistent customer history and knowledge base
2. Select Context - Retrieve relevant support articles and past interactions
3. Compress Context - Manage long support conversations 
4. Isolate Context - Separate contexts for different support channels/agents

Features:
- Customer profile persistence across sessions
- Support ticket lifecycle management  
- Knowledge base with context selection
- Multi-agent handoffs with context preservation
- Escalation workflows with context isolation

Usage:
    python examples/simple_customer_support.py
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from tinycontext.simple import ContextAgent


class CustomerSupportSystem:
    """Customer support system with context engineering patterns"""
    
    def __init__(self):
        self.primary_agent = None
        self.specialist_agents = {}
        self.customer_profiles = {}
        self.active_tickets = {}
        self.knowledge_base = {}
        
    async def initialize(self):
        """Initialize the support system"""
        print("🎧 Initializing Customer Support System...")
        
        # Primary support agent
        self.primary_agent = ContextAgent(
            name="primary_support",
            storage_path="./support_memory"
        )
        await self.primary_agent.initialize()
        
        # Load knowledge base (Write Context pattern)
        await self._load_knowledge_base()
        
        # Initialize specialist agents
        await self._initialize_specialists()
        
        print("✅ Customer Support System Ready!")
    
    async def _load_knowledge_base(self):
        """Load support knowledge base into persistent memory"""
        knowledge_articles = {
            "login_issues": {
                "content": "Common login issues: 1) Check password (case sensitive), 2) Clear browser cache, 3) Try incognito mode, 4) Reset password if needed. For 2FA issues, check time sync on device.",
                "tags": ["login", "authentication", "troubleshooting"],
                "priority": 3
            },
            "billing_disputes": {
                "content": "Billing dispute process: 1) Gather transaction details, 2) Check service usage logs, 3) Verify subscription status, 4) Escalate to billing team if amount > $100, 5) Issue refund if error confirmed.",
                "tags": ["billing", "refunds", "disputes"],
                "priority": 2
            },
            "password_reset": {
                "content": "Password reset steps: 1) Navigate to login page, 2) Click 'Forgot Password', 3) Enter email address, 4) Check email for reset link, 5) Create new secure password with 8+ chars, numbers, symbols.",
                "tags": ["password", "reset", "security"],
                "priority": 3
            },
            "account_suspension": {
                "content": "Account suspension reasons: Terms violation, payment failure, security concerns. Resolution: 1) Review suspension reason, 2) Address underlying issue, 3) Submit appeal if appropriate, 4) Wait for security team review.",
                "tags": ["suspension", "security", "compliance"],
                "priority": 1
            },
            "feature_requests": {
                "content": "Feature request handling: 1) Acknowledge request, 2) Log in product backlog, 3) Provide estimated timeline if available, 4) Suggest workarounds if possible, 5) Follow up quarterly on status.",
                "tags": ["features", "product", "enhancement"],
                "priority": 2
            }
        }
        
        print("  📚 Loading Knowledge Base...")
        for article_id, article_data in knowledge_articles.items():
            await self.primary_agent.add_context(
                f"kb_{article_id}",
                article_data["content"],
                article_data["tags"],
                persistent=True
            )
            
            # Also store in context selector with priority
            await self.primary_agent.context_selector.add_context(
                article_id,
                article_data["content"],
                article_data["tags"],
                article_data["priority"]
            )
            
            self.knowledge_base[article_id] = article_data
        
        print(f"    ✓ Loaded {len(knowledge_articles)} knowledge articles")
    
    async def _initialize_specialists(self):
        """Initialize specialist agents for escalations (Isolate Context pattern)"""
        specialists = {
            "billing_specialist": {
                "role": "billing and payments specialist",
                "expertise": ["billing", "refunds", "subscriptions", "payments"]
            },
            "security_specialist": {
                "role": "security and compliance specialist", 
                "expertise": ["security", "suspension", "compliance", "fraud"]
            },
            "technical_specialist": {
                "role": "technical support specialist",
                "expertise": ["technical", "integration", "api", "troubleshooting"]
            }
        }
        
        print("  👥 Initializing Specialist Agents...")
        for specialist_name, specialist_info in specialists.items():
            agent = ContextAgent(
                name=specialist_name,
                storage_path=f"./support_memory/{specialist_name}"
            )
            await agent.initialize()
            
            # Load specialist-specific knowledge
            for article_id, article_data in self.knowledge_base.items():
                if any(tag in specialist_info["expertise"] for tag in article_data["tags"]):
                    await agent.add_context(
                        f"kb_{article_id}",
                        article_data["content"],
                        article_data["tags"],
                        persistent=True
                    )
            
            self.specialist_agents[specialist_name] = {
                "agent": agent,
                "role": specialist_info["role"],
                "expertise": specialist_info["expertise"]
            }
            
            print(f"    ✓ {specialist_name} ready")
    
    async def create_customer_profile(self, 
                                    customer_id: str,
                                    name: str,
                                    email: str,
                                    plan: str = "basic") -> Dict:
        """Create persistent customer profile (Write Context pattern)"""
        profile = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "plan": plan,
            "created_at": datetime.now().isoformat(),
            "support_history": [],
            "preferences": {},
            "status": "active"
        }
        
        self.customer_profiles[customer_id] = profile
        
        # Store in persistent memory
        await self.primary_agent.context_writer.write_memory(
            f"customer_profile_{customer_id}",
            profile,
            metadata={"type": "customer_profile", "email": email}
        )
        
        print(f"👤 Created customer profile: {name} ({customer_id})")
        return profile
    
    async def create_support_ticket(self,
                                  customer_id: str,
                                  issue_description: str,
                                  priority: str = "normal",
                                  category: str = "general") -> str:
        """Create new support ticket with isolated context"""
        ticket_id = str(uuid.uuid4())[:8]
        
        # Create isolated context for this ticket
        ticket_schema = {
            "ticket_id": {"type": str},
            "customer_id": {"type": str},
            "issue": {"type": str},
            "priority": {"type": str},
            "category": {"type": str},
            "status": {"type": str},
            "assigned_agent": {"type": str},
            "conversation_history": {"type": list},
            "resolution": {"type": str},
            "escalation_history": {"type": list}
        }
        
        context_id = await self.primary_agent.create_isolated_context(
            f"ticket_{ticket_id}",
            ticket_schema
        )
        
        # Initialize ticket data
        ticket_data = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "issue": issue_description,
            "priority": priority,
            "category": category,
            "status": "open",
            "assigned_agent": "primary_support",
            "created_at": datetime.now().isoformat(),
            "conversation_history": [],
            "resolution": None,
            "escalation_history": []
        }
        
        # Store in isolated context
        for key, value in ticket_data.items():
            if key in ticket_schema:
                await self.primary_agent.context_isolator.write_to_context(
                    context_id, key, value
                )
        
        self.active_tickets[ticket_id] = {
            "data": ticket_data,
            "context_id": context_id
        }
        
        print(f"🎫 Created support ticket: {ticket_id}")
        print(f"   Customer: {customer_id}")
        print(f"   Issue: {issue_description[:100]}...")
        print(f"   Priority: {priority}")
        
        return ticket_id
    
    async def handle_support_request(self,
                                   ticket_id: str,
                                   customer_message: str) -> Dict:
        """Handle support request with context selection and compression"""
        if ticket_id not in self.active_tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket_info = self.active_tickets[ticket_id]
        customer_id = ticket_info["data"]["customer_id"]
        
        print(f"\n💬 Handling Support Request - Ticket {ticket_id}")
        print(f"   Message: {customer_message[:100]}...")
        
        # Get customer profile from persistent memory
        customer_profile = await self.primary_agent.context_writer.read_memory(
            f"customer_profile_{customer_id}"
        )
        
        # Select relevant knowledge base articles (Select Context pattern)
        relevant_kb = await self.primary_agent.context_selector.select_relevant(
            customer_message,
            max_contexts=3,
            max_tokens=1000
        )
        
        print(f"   📖 Found {len(relevant_kb)} relevant KB articles")
        
        # Get conversation history and compress if needed (Compress Context pattern)
        conversation_history = ticket_info["data"]["conversation_history"]
        if len(conversation_history) > 6:
            compressed_history = await self.primary_agent.context_compressor.compress_conversation(
                conversation_history,
                preserve_recent=3
            )
            print(f"   🗜️ Compressed conversation history ({len(conversation_history)} → {compressed_history['compressed_count']} messages)")
            history_context = compressed_history
        else:
            history_context = {"messages": conversation_history, "compressed": False}
        
        # Prepare context-rich support response
        support_task = f"""
        You are a customer support agent helping with ticket {ticket_id}.
        
        Customer Profile:
        - Name: {customer_profile.get('name', 'Unknown') if customer_profile else 'Unknown'}
        - Plan: {customer_profile.get('plan', 'basic') if customer_profile else 'basic'}
        - Email: {customer_profile.get('email', 'unknown') if customer_profile else 'unknown'}
        
        Customer Message: {customer_message}
        
        Relevant Knowledge Base:
        {chr(10).join([f"- {kb['content'][:200]}..." for kb in relevant_kb])}
        
        Previous Conversation Summary:
        {history_context.get('summary', 'No previous context') if history_context.get('compressed') else 'Recent conversation available'}
        
        Provide a helpful, professional response that:
        1. Addresses the customer's specific issue
        2. Uses relevant KB information
        3. Considers their account status and history
        4. Suggests next steps or escalation if needed
        """
        
        # Generate response
        result = await self.primary_agent.run(
            task=support_task,
            context_strategy="select",  # Use context selection
            data={
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "message": customer_message
            }
        )
        
        # Update ticket conversation history
        conversation_update = [
            {
                "timestamp": datetime.now().isoformat(),
                "role": "customer",
                "message": customer_message
            },
            {
                "timestamp": datetime.now().isoformat(),
                "role": "agent",
                "agent": "primary_support",
                "message": result["output"]
            }
        ]
        
        ticket_info["data"]["conversation_history"].extend(conversation_update)
        
        # Update isolated context
        await self.primary_agent.context_isolator.write_to_context(
            ticket_info["context_id"],
            "conversation_history",
            ticket_info["data"]["conversation_history"]
        )
        
        return {
            "ticket_id": ticket_id,
            "response": result["output"],
            "kb_articles_used": len(relevant_kb),
            "conversation_compressed": history_context.get("compressed", False),
            "escalation_needed": self._check_escalation_needed(customer_message, result["output"])
        }
    
    async def escalate_ticket(self,
                            ticket_id: str,
                            escalation_reason: str,
                            specialist_type: str = "auto") -> Dict:
        """Escalate ticket to specialist with context handoff"""
        if ticket_id not in self.active_tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Auto-detect specialist if not specified
        if specialist_type == "auto":
            specialist_type = self._determine_specialist(escalation_reason)
        
        if specialist_type not in self.specialist_agents:
            raise ValueError(f"Specialist {specialist_type} not available")
        
        print(f"\n🔄 Escalating Ticket {ticket_id} to {specialist_type}")
        print(f"   Reason: {escalation_reason}")
        
        ticket_info = self.active_tickets[ticket_id]
        specialist_info = self.specialist_agents[specialist_type]
        specialist_agent = specialist_info["agent"]
        
        # Create handoff context with all relevant information
        handoff_context = {
            "original_ticket": ticket_info["data"],
            "escalation_reason": escalation_reason,
            "specialist_expertise": specialist_info["expertise"],
            "handoff_timestamp": datetime.now().isoformat()
        }
        
        # Create isolated context for specialist
        specialist_context_id = await specialist_agent.create_isolated_context(
            f"escalated_{ticket_id}",
            {
                "original_ticket_id": {"type": str},
                "escalation_reason": {"type": str},
                "specialist_analysis": {"type": str},
                "specialist_resolution": {"type": str},
                "handoff_complete": {"type": bool}
            }
        )
        
        # Prepare specialist handoff task
        specialist_task = f"""
        You are a {specialist_info['role']} receiving an escalated support ticket.
        
        Original Ticket ID: {ticket_id}
        Escalation Reason: {escalation_reason}
        
        Customer Issue: {ticket_info['data']['issue']}
        Priority: {ticket_info['data']['priority']}
        
        Previous Conversation:
        {self._format_conversation_for_handoff(ticket_info['data']['conversation_history'])}
        
        As a specialist in {', '.join(specialist_info['expertise'])}, please:
        1. Analyze the escalated issue
        2. Provide specialized guidance or resolution
        3. Determine if further escalation is needed
        4. Suggest next steps for the customer
        """
        
        # Specialist handles the escalation
        specialist_result = await specialist_agent.run(
            task=specialist_task,
            context_strategy="isolate",  # Use context isolation
            data=handoff_context
        )
        
        # Update escalation history
        escalation_entry = {
            "timestamp": datetime.now().isoformat(),
            "escalated_to": specialist_type,
            "reason": escalation_reason,
            "specialist_response": specialist_result["output"]
        }
        
        ticket_info["data"]["escalation_history"].append(escalation_entry)
        ticket_info["data"]["assigned_agent"] = specialist_type
        
        # Update ticket status
        await self.primary_agent.context_isolator.write_to_context(
            ticket_info["context_id"],
            "escalation_history", 
            ticket_info["data"]["escalation_history"]
        )
        
        await self.primary_agent.context_isolator.write_to_context(
            ticket_info["context_id"],
            "assigned_agent",
            specialist_type
        )
        
        print(f"   ✅ Escalation completed")
        
        return {
            "ticket_id": ticket_id,
            "escalated_to": specialist_type,
            "specialist_response": specialist_result["output"],
            "escalation_complete": True
        }
    
    async def get_ticket_summary(self, ticket_id: str) -> Dict:
        """Get comprehensive ticket summary with context"""
        if ticket_id not in self.active_tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        ticket_info = self.active_tickets[ticket_id]
        
        # Get current context state
        context_summary = await self.primary_agent.context_isolator.get_context_summary(
            ticket_info["context_id"]
        )
        
        return {
            "ticket_data": ticket_info["data"],
            "context_summary": context_summary,
            "conversation_length": len(ticket_info["data"]["conversation_history"]),
            "escalation_count": len(ticket_info["data"]["escalation_history"]),
            "status": ticket_info["data"]["status"]
        }
    
    def _check_escalation_needed(self, customer_message: str, agent_response: str) -> bool:
        """Simple heuristic to check if escalation might be needed"""
        escalation_keywords = [
            "manager", "escalate", "unsatisfied", "complaint", 
            "legal", "lawsuit", "terrible", "worst", "cancel"
        ]
        return any(keyword in customer_message.lower() for keyword in escalation_keywords)
    
    def _determine_specialist(self, escalation_reason: str) -> str:
        """Auto-determine specialist type based on escalation reason"""
        reason_lower = escalation_reason.lower()
        
        if any(keyword in reason_lower for keyword in ["billing", "payment", "refund", "charge"]):
            return "billing_specialist"
        elif any(keyword in reason_lower for keyword in ["security", "suspension", "fraud", "hack"]):
            return "security_specialist"  
        elif any(keyword in reason_lower for keyword in ["technical", "api", "integration", "bug"]):
            return "technical_specialist"
        else:
            return "billing_specialist"  # Default
    
    def _format_conversation_for_handoff(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for specialist handoff"""
        if not conversation_history:
            return "No previous conversation"
        
        formatted = []
        for msg in conversation_history[-4:]:  # Last 4 messages
            role = msg.get("role", "unknown")
            content = msg.get("message", "")
            formatted.append(f"{role.upper()}: {content[:200]}...")
        
        return "\n".join(formatted)


async def demo_support_session():
    """Demo complete customer support session"""
    print("🎧 Customer Support System Demo - Context Engineering Showcase")
    print("=" * 65)
    
    # Initialize system
    support_system = CustomerSupportSystem()
    await support_system.initialize()
    
    # Create customer profile
    print("\n👤 Creating Customer Profile...")
    customer_id = "cust_12345"
    await support_system.create_customer_profile(
        customer_id=customer_id,
        name="Alice Johnson",
        email="alice@example.com", 
        plan="premium"
    )
    
    # Create support ticket
    print("\n🎫 Creating Support Ticket...")
    ticket_id = await support_system.create_support_ticket(
        customer_id=customer_id,
        issue_description="I can't log into my account. I keep getting an 'invalid password' error even though I'm sure my password is correct. This is very frustrating and I need access urgently for my business.",
        priority="high",
        category="login"
    )
    
    # Handle initial support request
    print("\n💬 Handling Initial Support Request...")
    response1 = await support_system.handle_support_request(
        ticket_id,
        "I've tried resetting my password twice but I still can't get in. The reset emails are taking forever to arrive and when they do, the links don't work properly. This is affecting my business operations!"
    )
    
    print(f"\n🤖 Agent Response:")
    print(response1["response"])
    print(f"KB Articles Used: {response1['kb_articles_used']}")
    print(f"Escalation Needed: {response1['escalation_needed']}")
    
    # Customer follows up
    print("\n💬 Customer Follow-up...")
    response2 = await support_system.handle_support_request(
        ticket_id,
        "The password reset still isn't working. I've cleared my cache, tried incognito mode, and even tried from a different computer. I'm getting really frustrated here. I want to speak to a manager about this terrible service!"
    )
    
    print(f"\n🤖 Agent Response:")
    print(response2["response"])
    print(f"Escalation Needed: {response2['escalation_needed']}")
    
    # Escalate to specialist
    if response2["escalation_needed"]:
        print("\n🔄 Escalating to Specialist...")
        escalation_result = await support_system.escalate_ticket(
            ticket_id,
            "Customer frustrated with repeated password reset failures, requesting manager, service quality complaint",
            specialist_type="auto"  # Auto-detect appropriate specialist
        )
        
        print(f"\n👨‍💼 Specialist Response:")
        print(escalation_result["specialist_response"])
    
    # Get final ticket summary
    print("\n📊 Final Ticket Summary...")
    summary = await support_system.get_ticket_summary(ticket_id)
    
    print(f"Ticket ID: {summary['ticket_data']['ticket_id']}")
    print(f"Status: {summary['ticket_data']['status']}")
    print(f"Assigned Agent: {summary['ticket_data']['assigned_agent']}")
    print(f"Conversation Messages: {summary['conversation_length']}")
    print(f"Escalations: {summary['escalation_count']}")
    
    return summary


async def interactive_support_mode():
    """Interactive customer support simulation"""
    print("\n🎧 Interactive Customer Support Mode")
    print("Simulate a customer support conversation!")
    
    support_system = CustomerSupportSystem()
    await support_system.initialize()
    
    # Create customer
    customer_name = input("Customer Name: ").strip() or "Test Customer"
    customer_email = input("Customer Email: ").strip() or "test@example.com"
    customer_id = f"cust_{customer_name.lower().replace(' ', '_')}"
    
    await support_system.create_customer_profile(
        customer_id=customer_id,
        name=customer_name,
        email=customer_email
    )
    
    # Create ticket
    print("\n🎫 Describe your issue:")
    issue = input("Issue: ").strip()
    if not issue:
        issue = "I need help with my account"
    
    ticket_id = await support_system.create_support_ticket(
        customer_id=customer_id,
        issue_description=issue
    )
    
    print(f"\n✅ Ticket created: {ticket_id}")
    print("Now chat with support! Type 'escalate' to request escalation, 'summary' for ticket summary, or 'quit' to exit.")
    
    while True:
        try:
            customer_msg = input(f"\n[{customer_name}]: ").strip()
            
            if customer_msg.lower() in ['quit', 'exit', 'q']:
                break
            elif customer_msg.lower() == 'escalate':
                reason = input("Escalation reason: ").strip() or "Customer requested escalation"
                escalation_result = await support_system.escalate_ticket(ticket_id, reason)
                print(f"\n[Specialist]: {escalation_result['specialist_response']}")
                continue
            elif customer_msg.lower() == 'summary':
                summary = await support_system.get_ticket_summary(ticket_id)
                print(f"\nTicket Summary:")
                print(f"- Messages: {summary['conversation_length']}")
                print(f"- Escalations: {summary['escalation_count']}")
                print(f"- Status: {summary['ticket_data']['status']}")
                continue
            
            if not customer_msg:
                continue
            
            # Handle support request
            response = await support_system.handle_support_request(ticket_id, customer_msg)
            print(f"\n[Support Agent]: {response['response']}")
            
            if response['escalation_needed']:
                print("\n⚠️  This conversation may benefit from escalation. Type 'escalate' to escalate.")
            
        except KeyboardInterrupt:
            print("\n\nSupport session ended. 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    print("TinyContext Customer Support - Context Engineering Demo")
    print("Choose mode:")
    print("1. Full demo (automated support session with escalation)")
    print("2. Interactive mode (simulate customer support conversation)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await demo_support_session()
        elif choice == "2":
            await interactive_support_mode()
        else:
            print("Invalid choice. Running full demo...")
            await demo_support_session()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in your environment (preferred for speed)")
        print("2. Or set OPENAI_API_KEY as fallback")
        print("3. Installed dependencies: pip install tinycontext")


if __name__ == "__main__":
    asyncio.run(main())