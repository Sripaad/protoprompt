#!/usr/bin/env python3
"""
Streamlined Chat Demo - Direct LLM conversation without ReAct overhead

This is a lightweight chat interface that bypasses the full framework's
agent_selection → tiny_reasoning → tiny_action pipeline for simple conversations.

Perfect for:
- Basic chat and Q&A
- Quick responses without workflow overhead  
- Testing raw Groq performance (~500 tokens/sec)
- Simple interactions that don't need multi-agent coordination

For complex tasks requiring workflows, use the full framework examples instead.

Usage:
    python examples/streamlined_chat.py
"""

import asyncio
import time
import os
from datetime import datetime
from groq import AsyncGroq


class StreamlinedChat:
    """Direct chat interface using Groq without framework overhead"""
    
    def __init__(self, name: str = "StreamlineBot"):
        self.name = name
        self.client = None
        self.conversation_history = []
        self.start_time = None
        self.message_count = 0
        
    async def initialize(self):
        """Initialize with direct Groq client"""
        print(f"⚡ Initializing {self.name} (Streamlined Mode)...")
        
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY environment variable required")
        
        self.client = AsyncGroq(api_key=groq_key)
        self.start_time = datetime.now()
        
        print(f"✅ {self.name} ready! (Direct Groq • ~500 tok/sec)")
        
    async def chat_loop(self):
        """Streamlined chat loop with single LLM calls"""
        print(f"\n⚡ Streamlined Chat with {self.name}")
        print("=" * 50)
        print("Direct Groq inference - no agent selection overhead!")
        print("Commands: 'quit', 'history', 'stats', 'clear'")
        print()
        
        while True:
            try:
                user_input = input(f"🧑 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    await self._end_chat()
                    break
                    
                elif user_input.lower() == 'history':
                    self._show_history()
                    continue
                    
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                    
                elif user_input.lower() == 'clear':
                    self._clear_history()
                    continue
                
                if not user_input:
                    continue
                
                # Single direct call - no ReAct overhead
                await self._handle_message(user_input)
                
            except KeyboardInterrupt:
                print("\n\nChat ended. Goodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def _handle_message(self, user_input: str):
        """Handle message with direct Groq call"""
        start_time = time.time()
        
        print(f"⚡ {self.name}: ", end="", flush=True)
        
        try:
            # Build conversation context
            messages = self._build_conversation_context(user_input)
            
            # Direct streaming call to Groq
            stream = await self.client.chat.completions.create(
                model="openai/gpt-oss-120b",  # Your fast model
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=True  # Enable streaming for speed
            )
            
            # Stream response in real-time
            response_chunks = []
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    response_chunks.append(content)
            
            full_response = ''.join(response_chunks)
            end_time = time.time()
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": start_time
            })
            
            self.conversation_history.append({
                "role": "assistant", 
                "content": full_response,
                "timestamp": end_time
            })
            
            # Show performance stats
            duration = end_time - start_time
            token_count = len(full_response.split())
            tokens_per_sec = token_count / duration if duration > 0 else 0
            
            print(f"\n   ⚡ {tokens_per_sec:.1f} tok/sec • {duration:.2f}s • direct call")
            
            self.message_count += 1
            
        except Exception as e:
            print(f"❌ Failed: {e}")
        
        print()  # Extra line for readability
    
    def _build_conversation_context(self, user_input: str) -> list:
        """Build conversation context for the LLM"""
        messages = [
            {
                "role": "system",
                "content": f"You are {self.name}, a helpful AI assistant. Be conversational, helpful, and concise. Remember the conversation context."
            }
        ]
        
        # Add recent conversation history (last 6 messages for context)
        recent_history = self.conversation_history[-6:] if len(self.conversation_history) > 6 else self.conversation_history
        
        for msg in recent_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user", 
            "content": user_input
        })
        
        return messages
    
    def _show_history(self):
        """Show recent conversation history"""
        print(f"\n💭 Recent Conversation ({min(5, len(self.conversation_history))} messages)")
        
        if not self.conversation_history:
            print("   No messages yet")
            return
        
        # Show last 5 messages
        recent = self.conversation_history[-5:]
        for msg in recent:
            role_emoji = "🧑" if msg["role"] == "user" else "⚡"
            content = msg["content"][:80] + "..." if len(msg["content"]) > 80 else msg["content"]
            print(f"   {role_emoji} {content}")
        
        print()
    
    def _show_stats(self):
        """Show performance statistics"""
        print(f"\n📊 Chat Statistics")
        
        if self.start_time:
            session_duration = (datetime.now() - self.start_time).total_seconds()
            print(f"   Session duration: {session_duration:.1f}s")
            print(f"   Messages exchanged: {self.message_count}")
            
            if self.message_count > 0:
                avg_time = session_duration / self.message_count
                print(f"   Average response time: {avg_time:.2f}s")
        
        print(f"   Mode: Streamlined (Direct Groq)")
        print(f"   Model: openai/gpt-oss-120b")
        print(f"   History length: {len(self.conversation_history)} messages")
        print()
    
    def _clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.message_count = 0
        print("🗑️ Conversation history cleared")
        print()
    
    async def _end_chat(self):
        """End chat with summary"""
        print(f"\n👋 Ending streamlined chat")
        
        if self.message_count > 0:
            session_duration = (datetime.now() - self.start_time).total_seconds()
            avg_response = session_duration / self.message_count
            
            print(f"   📊 Session Stats:")
            print(f"   • Duration: {session_duration:.1f}s")
            print(f"   • Messages: {self.message_count}")
            print(f"   • Avg response: {avg_response:.2f}s")
            print(f"   • Mode: Direct Groq (no ReAct overhead)")
        
        print("   Thanks for trying streamlined chat! ⚡")


async def quick_chat_test():
    """Quick automated test of streamlined chat"""
    print("⚡ Quick Streamlined Chat Test")
    print("=" * 35)
    
    chat = StreamlinedChat("QuickTest")
    await chat.initialize()
    
    # Quick test messages
    test_messages = [
        "Hello! How fast are you?",
        "What's 15 * 23?", 
        "Can you remember what I asked before?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🧑 Test {i}: {message}")
        await chat._handle_message(message)
    
    print("\n✅ Streamlined chat test complete!")
    chat._show_stats()


async def interactive_streamlined_chat():
    """Full interactive streamlined chat"""
    print("⚡ Interactive Streamlined Chat")
    print("=" * 40)
    
    bot_name = input("Bot name (or Enter for 'StreamlineBot'): ").strip()
    if not bot_name:
        bot_name = "StreamlineBot"
    
    chat = StreamlinedChat(bot_name)
    await chat.initialize()
    
    await chat.chat_loop()


async def main():
    """Main entry point"""
    print("TinyContext Streamlined Chat Demo")
    print("Direct Groq inference without ReAct overhead")
    print("\nChoose mode:")
    print("1. Quick test (automated conversation)")
    print("2. Interactive chat (streamlined mode)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await quick_chat_test()
        elif choice == "2":
            await interactive_streamlined_chat()
        else:
            print("Invalid choice. Running quick test...")
            await quick_chat_test()
            
    except KeyboardInterrupt:
        print("\n\nDemo interrupted. Goodbye! 👋")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Set GROQ_API_KEY in your environment")
        print("2. Installed: pip install groq")


if __name__ == "__main__":
    asyncio.run(main())