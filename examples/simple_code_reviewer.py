#!/usr/bin/env python3
"""
Code Reviewer Example - Context Isolation Showcase

This example demonstrates context isolation patterns with a code reviewer that:
1. Isolates context for different files/modules (Isolate Context)
2. Maintains separate analysis contexts for different review aspects
3. Compresses large codebases for efficient review (Compress Context) 
4. Writes persistent review guidelines and standards (Write Context)

Usage:
    python examples/simple_code_reviewer.py
"""

import asyncio
from pathlib import Path
from typing import Dict, List
from tinycontext.simple import ContextAgent


class CodeReviewSession:
    """Code review session with isolated contexts per file and review aspect"""
    
    def __init__(self):
        self.reviewer = None
        self.review_contexts = {}
        self.code_files = {}
        
    async def initialize(self):
        """Initialize the code reviewer"""
        self.reviewer = ContextAgent(
            name="code_reviewer",
            storage_path="./code_review_memory"
        )
        await self.reviewer.initialize()
        
        # Load review guidelines into persistent memory
        await self._load_review_standards()
        
    async def _load_review_standards(self):
        """Load code review standards and guidelines (Write Context pattern)"""
        review_guidelines = {
            "security": {
                "content": "Check for SQL injection, XSS vulnerabilities, input validation, authentication issues, and secrets in code.",
                "tags": ["security", "guidelines"]
            },
            "performance": {
                "content": "Look for inefficient algorithms, memory leaks, unnecessary loops, database N+1 queries, and blocking operations.",
                "tags": ["performance", "guidelines"] 
            },
            "maintainability": {
                "content": "Assess code readability, function length, naming conventions, documentation, and adherence to SOLID principles.",
                "tags": ["maintainability", "guidelines"]
            },
            "testing": {
                "content": "Verify test coverage, test quality, edge cases, mocking strategies, and test organization.",
                "tags": ["testing", "guidelines"]
            }
        }
        
        print("📋 Loading Review Standards...")
        for standard_name, standard_data in review_guidelines.items():
            await self.reviewer.add_context(
                f"review_standard_{standard_name}",
                standard_data["content"],
                standard_data["tags"],
                persistent=True
            )
            print(f"  ✓ Loaded {standard_name} guidelines")
    
    async def add_code_file(self, file_path: str, content: str = None):
        """Add a code file for review with isolated context"""
        if content is None and Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        if not content:
            raise ValueError(f"Could not load content for {file_path}")
        
        # Create isolated context for this file
        file_id = Path(file_path).stem
        context_schema = {
            "file_path": {"type": str},
            "content": {"type": str},
            "language": {"type": str},
            "security_issues": {"type": list},
            "performance_issues": {"type": list},
            "maintainability_issues": {"type": list},
            "testing_issues": {"type": list},
            "overall_score": {"type": float}
        }
        
        context_id = await self.reviewer.create_isolated_context(
            f"file_{file_id}", 
            context_schema
        )
        
        # Store file info in isolated context
        await self.reviewer.context_isolator.write_to_context(
            context_id, "file_path", file_path
        )
        await self.reviewer.context_isolator.write_to_context(
            context_id, "content", content
        )
        await self.reviewer.context_isolator.write_to_context(
            context_id, "language", self._detect_language(file_path)
        )
        
        self.code_files[file_id] = {
            "path": file_path,
            "context_id": context_id,
            "content": content
        }
        
        print(f"📁 Added file for review: {file_path}")
        return file_id
    
    async def review_file(self, file_id: str, review_aspects: List[str] = None) -> Dict:
        """Review a specific file with isolated contexts for each aspect"""
        if file_id not in self.code_files:
            raise ValueError(f"File {file_id} not found")
        
        file_info = self.code_files[file_id]
        review_aspects = review_aspects or ["security", "performance", "maintainability", "testing"]
        
        print(f"\n🔍 Reviewing {file_info['path']}...")
        
        review_results = {}
        
        for aspect in review_aspects:
            print(f"  Analyzing {aspect}...")
            
            # Create isolated context for this review aspect
            aspect_context_id = await self.reviewer.create_isolated_context(
                f"{file_id}_{aspect}",
                {
                    "aspect": {"type": str},
                    "file_content": {"type": str},
                    "issues": {"type": list},
                    "suggestions": {"type": list},
                    "score": {"type": float}
                }
            )
            
            # Prepare context-specific review prompt
            review_task = f"""
            Review this {file_info.get('language', 'code')} file focusing specifically on {aspect}.
            
            File: {file_info['path']}
            Content: {file_info['content'][:2000]}{'...' if len(file_info['content']) > 2000 else ''}
            
            Please provide:
            1. Specific {aspect} issues found
            2. Recommendations for improvement
            3. A score from 1-10 for {aspect} quality
            """
            
            result = await self.reviewer.run(
                task=review_task,
                context_strategy="isolate",  # Use context isolation
                data={
                    "file_path": file_info['path'],
                    "aspect": aspect,
                    "language": self._detect_language(file_info['path'])
                }
            )
            
            review_results[aspect] = {
                "analysis": result['output'],
                "context_id": aspect_context_id,
                "success": result['success']
            }
        
        return review_results
    
    async def comprehensive_review(self, compress_large_files: bool = True) -> Dict:
        """Perform comprehensive review of all files with context compression"""
        print(f"\n🎯 Comprehensive Code Review ({len(self.code_files)} files)")
        
        all_reviews = {}
        compressed_summaries = []
        
        for file_id, file_info in self.code_files.items():
            # Compress large files before review
            content = file_info['content']
            if compress_large_files and len(content) > 5000:
                print(f"  🗜️ Compressing large file: {file_info['path']}")
                compressed_content = await self.reviewer.context_compressor.compress_text(
                    content, target_length=2000
                )
                
                # Store compressed version for review
                file_info['compressed_content'] = compressed_content
                compressed_summaries.append(f"Compressed {file_info['path']} from {len(content)} to {len(compressed_content)} chars")
            
            # Review with compressed context if needed
            review_results = await self.review_file(file_id)
            all_reviews[file_id] = review_results
        
        # Generate overall project summary
        print("\n📊 Generating Project Summary...")
        
        summary_task = f"""
        Create a comprehensive code review summary for this project.
        
        Files reviewed: {len(all_reviews)}
        Review aspects: security, performance, maintainability, testing
        
        {'. '.join(compressed_summaries) if compressed_summaries else ''}
        
        Please provide:
        1. Overall project health score (1-10)
        2. Top 5 critical issues across all files
        3. Recommended next steps
        4. Positive aspects worth highlighting
        """
        
        summary_result = await self.reviewer.run(
            task=summary_task,
            context_strategy="compress",  # Use context compression for summary
            data={"review_count": len(all_reviews)},
            max_iterations=1
        )
        
        return {
            "file_reviews": all_reviews,
            "project_summary": summary_result['output'],
            "compressed_files": len(compressed_summaries),
            "total_files": len(all_reviews)
        }
    
    async def get_review_history(self) -> List[Dict]:
        """Get compressed review history"""
        return await self.reviewer.get_conversation_history(compressed=True)
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript', 
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        return language_map.get(ext, 'Unknown')


async def demo_with_sample_code():
    """Demo with sample code files"""
    print("🔧 Code Reviewer Demo - Context Isolation Showcase")
    print("=" * 55)
    
    # Create sample code files for demo
    sample_files = {
        "user_auth.py": '''
import hashlib
import sqlite3

def authenticate_user(username, password):
    # Security issue: SQL injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    # Performance issue: not closing connection
    return result is not None

def hash_password(password):
    # Security issue: using MD5 which is weak
    return hashlib.md5(password.encode()).hexdigest()

class UserManager:
    def __init__(self):
        self.users = []
        
    # Maintainability issue: method too long, no documentation
    def create_user(self, username, password, email, first_name, last_name, age, phone, address):
        if len(username) < 3:
            return False
        if len(password) < 8:
            return False
        hashed_password = hash_password(password)
        user = {
            "username": username,
            "password": hashed_password, 
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "phone": phone,
            "address": address
        }
        self.users.append(user)
        return True
        ''',
        
        "data_processor.js": '''
// Performance issues: inefficient algorithms
function processLargeDataset(data) {
    let results = [];
    
    // O(n²) complexity issue
    for (let i = 0; i < data.length; i++) {
        for (let j = 0; j < data.length; j++) {
            if (data[i].id === data[j].parentId) {
                results.push({parent: data[i], child: data[j]});
            }
        }
    }
    
    // Memory issue: creating many intermediate arrays
    return results.map(item => {
        return {
            ...item,
            processed: true,
            timestamp: new Date()
        };
    }).filter(item => item.parent.active).sort((a, b) => a.parent.id - b.parent.id);
}

// Testing issue: no error handling, no input validation
async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
}
        ''',
        
        "calculator.py": '''
# Good example with proper structure
class Calculator:
    """
    A simple calculator class demonstrating good practices.
    """
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers and record in history."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers with proper error handling."""
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        
        if b == 0:
            raise ValueError("Cannot divide by zero")
        
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self) -> list:
        """Get calculation history."""
        return self.history.copy()
        '''
    }
    
    # Initialize review session
    session = CodeReviewSession()
    await session.initialize()
    
    # Add sample files
    print("\n📁 Adding Sample Files...")
    for filename, content in sample_files.items():
        await session.add_code_file(filename, content)
    
    # Review individual files
    print("\n🔍 Individual File Reviews (Context Isolation)")
    for file_id in session.code_files.keys():
        print(f"\n--- Reviewing {file_id} ---")
        reviews = await session.review_file(file_id, ["security", "performance"])
        
        for aspect, review_data in reviews.items():
            if review_data['success']:
                print(f"  {aspect.upper()}: {review_data['analysis'][:200]}...")
            else:
                print(f"  {aspect.upper()}: Review failed")
    
    # Comprehensive review with compression
    print("\n📊 Comprehensive Review (Context Compression)")
    comprehensive_results = await session.comprehensive_review(compress_large_files=True)
    
    print(f"\n📋 Project Summary:")
    print(comprehensive_results['project_summary'])
    
    print(f"\nReview Statistics:")
    print(f"  Files reviewed: {comprehensive_results['total_files']}")
    print(f"  Files compressed: {comprehensive_results['compressed_files']}")
    
    # Show review history compression
    history = await session.get_review_history()
    print(f"  Conversation history: {len(history)} messages")
    
    return comprehensive_results


async def interactive_code_review():
    """Interactive mode for reviewing user's actual code files"""
    print("\n🤖 Interactive Code Review Mode")
    print("Provide file paths to review your actual code!")
    
    session = CodeReviewSession()
    await session.initialize()
    
    while True:
        try:
            file_path = input("\n📁 Enter file path (or 'done' to finish, 'quit' to exit): ").strip()
            
            if file_path.lower() in ['quit', 'exit', 'q']:
                break
            elif file_path.lower() in ['done', 'finish']:
                if session.code_files:
                    print("\n🎯 Running comprehensive review...")
                    results = await session.comprehensive_review()
                    print(f"\n📋 Final Summary:\n{results['project_summary']}")
                break
            
            if not file_path or not Path(file_path).exists():
                print("❌ File not found or invalid path")
                continue
            
            # Add file and review
            file_id = await session.add_code_file(file_path)
            
            print("Select review aspects (comma-separated):")
            print("1. security, 2. performance, 3. maintainability, 4. testing, 5. all")
            aspects_input = input("Enter choice: ").strip()
            
            if aspects_input == "5" or aspects_input.lower() == "all":
                aspects = ["security", "performance", "maintainability", "testing"]
            else:
                aspect_map = {"1": "security", "2": "performance", "3": "maintainability", "4": "testing"}
                aspects = [aspect_map.get(a.strip(), a.strip()) for a in aspects_input.split(",")]
                aspects = [a for a in aspects if a in ["security", "performance", "maintainability", "testing"]]
            
            if aspects:
                reviews = await session.review_file(file_id, aspects)
                for aspect, review_data in reviews.items():
                    print(f"\n📋 {aspect.upper()} REVIEW:")
                    print(review_data['analysis'])
            
        except KeyboardInterrupt:
            print("\n\nReview session ended. 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    print("TinyContext Code Reviewer - Context Isolation Demo")
    print("Choose mode:")
    print("1. Demo with sample code (showcases context isolation)")
    print("2. Interactive mode (review your actual files)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            await demo_with_sample_code()
        elif choice == "2": 
            await interactive_code_review()
        else:
            print("Invalid choice. Running sample demo...")
            await demo_with_sample_code()
            
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