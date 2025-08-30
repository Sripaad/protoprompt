#!/usr/bin/env python3
"""
Basic Chat Demo - Simple Interactive Conversation

A straightforward chat interface showcasing TinyContext Simple API with:
- Real-time conversation with context memory
- Automatic context engineering (Write, Select, Compress, Isolate)
- High-speed Groq inference (~500 tokens/sec)
- Persistent conversation history
- Easy switching between simple and full framework modes

Usage:
    python examples/basic_chat_demo.py
"""

import asyncio
import time
from datetime import datetime
from tinycontext.simple import ContextAgent


class BasicChatBot:
    """Simple chat bot with context engineering"""
    
    def __init__(self, name: str = "ChatBot"):
        self.name = name
        self.agent = None
        self.start_time = None
        self.message_count = 0
        
    async def initialize(self):
        """Initialize the chat bot"""
        print(f"🤖 Initializing {self.name}...")
        
        self.agent = ContextAgent(
            name="chat_agent",
            storage_path="./chat_memory"
        )
        await self.agent.initialize()
        
        # Add some initial context about the chat bot
        await self.agent.add_context(
            "chat_personality",
            f"You are {self.name}, a helpful AI assistant created with TinyContext. You use context engineering to provide better responses by remembering conversation history and relevant information.",
            ["personality", "chat"],
            persistent=True
        )
        
        await self.agent.add_context(
            "capabilities",
            "You can help with analysis, research, coding, planning, creative tasks, and general questions. You remember previous parts of our conversation and can build on them.",
            ["capabilities", "features"],
            persistent=True
        )
        
        self.start_time = datetime.now()
        print(f"✅ {self.name} ready! (Framework: TinyContext)")
        
    async def chat_loop(self):
        """Main chat interaction loop"""
        print(f"\n💬 Chat with {self.name}")
        print("=" * 40)
        print("Type your messages below. Use these special commands:")
        print("  'quit' or 'exit' - End conversation")
        print("  'history' - Show conversation summary") 
        print("  'context' - Show stored context")
        print("  'stats' - Show performance stats")
        print("  'clear' - Clear conversation history")
        print()
        
        while True:
            try:
                # Get user input
                user_input = input(f"🧑 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    await self._end_conversation()
                    break
                    
                elif user_input.lower() == 'history':
                    await self._show_history()
                    continue
                    
                elif user_input.lower() == 'context':
                    await self._show_context()
                    continue
                    
                elif user_input.lower() == 'stats':
                    await self._show_stats()
                    continue
                    
                elif user_input.lower() == 'clear':
                    await self._clear_history()
                    continue
                
                if not user_input:
                    continue
                
                # Generate response with timing
                await self._handle_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\nChat interrupted. Goodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Chat continues...")
    
    async def _handle_message(self, user_input: str):
        """Handle a single chat message with timing"""
        start_time = time.time()
        
        # Show thinking indicator
        print(f"🤖 {self.name}: ", end="", flush=True)
        print("💭 thinking...", end="", flush=True)
        
        # Determine context strategy based on conversation length
        strategy = "auto"
        if self.message_count > 10:
            strategy = "compress"  # Use compression for long conversations
        elif self.message_count > 5:
            strategy = "select"    # Use selection for medium conversations
        
        # Get response
        result = await self.agent.run(
            task=user_input,
            context_strategy=strategy,
            data={
                "message_number": self.message_count + 1,
                "conversation_context": "casual_chat"
            }
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Clear thinking indicator and show response
        print(f"\r🤖 {self.name}: ", end="")
        
        if result["success"]:
            response = result["output"]
            print(response)
            
            # Show performance info
            token_count = len(response.split())
            tokens_per_sec = token_count / duration if duration > 0 else 0
            print(f"   ⚡ {tokens_per_sec:.1f} tok/sec • {duration:.1f}s • {strategy} context")
            
        else:
            print(f"❌ Sorry, I encountered an error: {result.get('error', 'Unknown error')}")
        
        self.message_count += 1
        print()  # Extra line for readability
    
    async def _show_history(self):
        """Show conversation history summary"""
        print(f"\n📚 Conversation History ({self.message_count} messages)")
        
        if self.message_count == 0:
            print("   No messages yet")
            return
        
        # Get compressed history
        history = await self.agent.get_conversation_history(compressed=True)
        
        print(f"   Total messages: {len(history)}")
        if len(history) > 0:
            print(f"   Latest: {history[-1].get('content', 'No content')[:100]}...")
        
        # Show memory usage
        memories = await self.agent.context_writer.list_memories()
        print(f"   Persistent memories: {len(memories)}")
        print()
    
    async def _show_context(self):
        """Show stored context information"""
        print(f"\n🧠 Context Information")
        
        memories = await self.agent.context_writer.list_memories()
        print(f"   Stored memories: {len(memories)}")
        
        for memory in memories[:5]:  # Show first 5
            content = await self.agent.context_writer.read_memory(memory)
            if content:
                preview = str(content)[:80] + "..." if len(str(content)) > 80 else str(content)
                print(f"   - {memory}: {preview}")
        
        if len(memories) > 5:
            print(f"   ... and {len(memories) - 5} more")
        print()
    
    async def _show_stats(self):
        """Show performance and usage statistics"""
        print(f"\n📊 Chat Statistics")
        
        if self.start_time:
            session_duration = (datetime.now() - self.start_time).total_seconds()
            print(f"   Session duration: {session_duration:.1f} seconds")
            
            if self.message_count > 0:
                avg_time_per_message = session_duration / self.message_count
                print(f"   Messages: {self.message_count}")
                print(f"   Average response time: {avg_time_per_message:.1f}s")
        
        # Context stats
        memories = await self.agent.context_writer.list_memories()
        print(f"   Context memories: {len(memories)}")
        
        # Framework info
        framework = "Full TinyContext" if self.agent.use_full_framework else "Simple Mode"
        print(f"   Framework: {framework}")
        print(f"   Agent name: {self.agent.name}")
        print()
    
    async def _clear_history(self):
        """Clear conversation history"""
        self.agent.conversation_history = []
        self.message_count = 0
        print("🗑️ Conversation history cleared")
        print()
    
    async def _end_conversation(self):
        """End conversation with summary"""
        print(f"\n👋 Ending conversation with {self.name}")
        
        if self.message_count > 0:
            session_duration = (datetime.now() - self.start_time).total_seconds()
            print(f"   Session duration: {session_duration:.1f} seconds")
            print(f"   Messages exchanged: {self.message_count}")
            print(f"   Average response time: {session_duration / self.message_count:.1f}s")
        
        print("   Thanks for trying TinyContext! 🎉")


async def quick_chat_demo():
    """Quick demo conversation to show capabilities"""
    print("🚀 Quick Chat Demo - TinyContext in Action")
    print("=" * 45)
    
    bot = BasicChatBot("QuickDemo")
    await bot.initialize()
    
    # Pre-scripted demo conversation
    demo_messages = [
        "Hello! What can you do?",
        "Can you help me plan a project?", 
        "What about analyzing data?",
        "Remember what we talked about projects earlier?",
        "Great! Now create a quick summary of our conversation"
    ]
    
    for i, message in enumerate(demo_messages, 1):
        print(f"🧑 Demo Message {i}: {message}")
        await bot._handle_message(message)
        
        # Brief pause between messages
        await asyncio.sleep(1)
    
    print("\n✅ Quick demo complete!")
    
    # Show final stats
    await bot._show_stats()


async def interactive_chat():
    """Full interactive chat mode"""
    print("💬 Interactive Chat Mode")
    print("=" * 30)
    
    bot_name = input("Chat bot name (or press Enter for 'TinyBot'): ").strip()
    if not bot_name:
        bot_name = "TinyBot"
    
    bot = BasicChatBot(bot_name)
    await bot.initialize()
    
    await bot.chat_loop()


async def main():
    """Main entry point"""
    print("TinyContext Basic Chat Demo")
    print("High-speed inference with context engineering")
    print("\nChoose mode:")
    print("1. Quick demo (automated conversation)")
    print("2. Interactive chat (talk with the bot)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await quick_chat_demo()
        elif choice == "2":
            await interactive_chat()
        else:
            print("Invalid choice. Running quick demo...")
            await quick_chat_demo()
            
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