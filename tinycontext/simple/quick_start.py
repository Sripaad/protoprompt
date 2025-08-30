"""
Quick Start Setup - Zero-config initialization for TinyContext Simple

This module provides automatic setup and configuration detection for the simplest
possible getting started experience. Implements 12-factor agent principles:
- Zero manual configuration
- Environment-based settings  
- Graceful degradation
- Clear error messages

Usage:
    from tinycontext.simple import quick_start
    agent = quick_start()
    result = await agent.run("Hello world!")
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .context_agent import ContextAgent

# Configure logging
logger = logging.getLogger("tinycontext.simple.quick_start")


def quick_start(name: str = "quickstart_agent", 
               verbose: bool = None,
               storage_path: str = None) -> ContextAgent:
    """
    Zero-config setup for TinyContext Simple
    
    Auto-detects:
    - OpenAI API key from environment
    - TensorZero observability availability
    - Full framework vs simple mode
    - Storage location
    
    Args:
        name: Agent name (default: "quickstart_agent")
        verbose: Enable verbose logging (auto-detected from env)
        storage_path: Storage path (auto-detected)
        
    Returns:
        Configured ContextAgent ready to use
        
    Example:
        ```python
        agent = quick_start()
        result = await agent.run("Analyze this data", data={"values": [1,2,3]})
        ```
    """
    # Auto-detect verbose mode
    if verbose is None:
        verbose = os.getenv("TINYCONTEXT_VERBOSE", "false").lower() == "true"
    
    # Configure logging level
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        logger.info("Verbose mode enabled")
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Auto-detect storage path
    if storage_path is None:
        storage_path = _detect_storage_path()
    
    logger.debug(f"Using storage path: {storage_path}")
    
    # Check prerequisites
    _check_prerequisites()
    
    # Create agent with auto-detected settings
    agent = ContextAgent(
        name=name,
        storage_path=storage_path,
        use_full_framework=_detect_full_framework(),
        enable_observability=_detect_observability()
    )
    
    logger.info(f"Quick start agent '{name}' created")
    return agent


def setup_environment() -> Dict[str, Any]:
    """
    Interactive environment setup helper
    
    Guides users through setting up their environment with all necessary
    configuration for TinyContext Simple.
    
    Returns:
        Dict with setup status and recommendations
    """
    print("🚀 TinyContext Simple - Environment Setup")
    print("=" * 45)
    
    setup_status = {
        "openai_key": False,
        "dependencies": False,
        "storage": False,
        "observability": False,
        "recommendations": []
    }
    
    # Check OpenAI API Key
    print("\n🔑 Checking OpenAI API Key...")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("  ✅ OPENAI_API_KEY found")
        setup_status["openai_key"] = True
    else:
        print("  ❌ OPENAI_API_KEY not found")
        print("     Set it with: export OPENAI_API_KEY='your-key-here'")
        setup_status["recommendations"].append("Set OPENAI_API_KEY environment variable")
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    try:
        import openai
        print("  ✅ OpenAI package available")
        setup_status["dependencies"] = True
    except ImportError:
        print("  ❌ OpenAI package not found")
        print("     Install with: pip install openai")
        setup_status["recommendations"].append("Install OpenAI: pip install openai")
    
    # Check optional full framework
    try:
        from ..manager.async_context_manager import AsyncTinyContextManager
        print("  ✅ Full TinyContext framework available")
    except ImportError:
        print("  ⚠️  Full framework not available (simple mode only)")
        setup_status["recommendations"].append("For advanced features, install full dependencies")
    
    # Check storage
    print("\n💾 Checking Storage...")
    storage_path = _detect_storage_path()
    if Path(storage_path).parent.exists():
        print(f"  ✅ Storage path available: {storage_path}")
        setup_status["storage"] = True
    else:
        print(f"  ❌ Storage path not writable: {storage_path}")
        setup_status["recommendations"].append("Ensure write permissions for storage directory")
    
    # Check observability
    print("\n📊 Checking Observability...")
    if _detect_observability():
        print("  ✅ TensorZero observability enabled")
        setup_status["observability"] = True
    else:
        print("  ⚠️  TensorZero observability disabled")
        print("     Enable with: export ENABLE_OBSERVABILITY=true")
    
    # Summary
    print(f"\n📋 Setup Summary")
    ready = setup_status["openai_key"] and setup_status["dependencies"] and setup_status["storage"]
    
    if ready:
        print("  🎉 Ready to use TinyContext Simple!")
        print("  Try: from tinycontext.simple import quick_start")
    else:
        print("  ⚠️  Setup incomplete. Please address:")
        for rec in setup_status["recommendations"]:
            print(f"    - {rec}")
    
    return setup_status


def create_example_env_file(path: str = ".env") -> bool:
    """Create example .env file with TinyContext Simple configuration"""
    env_content = """# TinyContext Simple Configuration
# Copy this to .env and fill in your values

# Preferred: Groq API Key for high-speed inference (~500 tokens/sec)
GROQ_API_KEY=your-groq-api-key-here

# Fallback: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Enable verbose logging
TINYCONTEXT_VERBOSE=false

# Optional: Enable TensorZero observability
ENABLE_OBSERVABILITY=false

# Optional: TensorZero model (if using observability)
TENSORZERO_MODEL=groq

# Optional: Storage path for persistent context
TINYCONTEXT_STORAGE_PATH=./.tinycontext_memory
"""
    
    try:
        with open(path, 'w') as f:
            f.write(env_content)
        print(f"📝 Created example environment file: {path}")
        print("   Edit this file and set your OPENAI_API_KEY")
        return True
    except Exception as e:
        print(f"❌ Failed to create {path}: {e}")
        return False


def _detect_storage_path() -> str:
    """Auto-detect appropriate storage path"""
    # Check environment variable first
    env_path = os.getenv("TINYCONTEXT_STORAGE_PATH")
    if env_path:
        return env_path
    
    # Check for common project directories
    current_dir = Path.cwd()
    
    # If we're in a project with pyproject.toml or setup.py, use project-local storage
    if (current_dir / "pyproject.toml").exists() or (current_dir / "setup.py").exists():
        return str(current_dir / ".tinycontext_memory")
    
    # Check if we can write to current directory
    if os.access(current_dir, os.W_OK):
        return str(current_dir / ".tinycontext_memory")
    
    # Fall back to user home directory
    home_dir = Path.home()
    return str(home_dir / ".tinycontext" / "memory")


def _detect_full_framework() -> bool:
    """Detect if full TinyContext framework is available"""
    try:
        from ..manager.async_context_manager import AsyncTinyContextManager
        from ..agents.proto_factory import ProtoFactory
        return True
    except ImportError:
        return False


def _detect_observability() -> bool:
    """Detect if observability should be enabled"""
    # Check explicit environment variable
    env_setting = os.getenv("ENABLE_OBSERVABILITY", "").lower()
    if env_setting in ["true", "1", "yes"]:
        return True
    elif env_setting in ["false", "0", "no"]:
        return False
    
    # Auto-detect based on TensorZero availability
    try:
        import tensorzero
        # If TensorZero is installed and we have a model configured, enable observability
        return bool(os.getenv("TENSORZERO_MODEL"))
    except ImportError:
        return False


def _check_prerequisites() -> None:
    """Check and warn about missing prerequisites"""
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 11):
        issues.append("Python 3.11+ required (current: {}.{})".format(
            sys.version_info.major, sys.version_info.minor
        ))
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("OPENAI_API_KEY environment variable not set")
    
    # Check OpenAI package
    try:
        import openai
        # Test that we can create a client
        openai.AsyncOpenAI(api_key="test")
    except ImportError:
        issues.append("OpenAI package not installed (pip install openai)")
    except Exception:
        # OpenAI package is installed, just can't create client without key
        pass
    
    if issues:
        logger.warning("Prerequisites issues detected:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it in your .env file or environment."
            )


# Convenience function for one-line usage
async def run_quick_task(task: str, data: Optional[Dict] = None, **kwargs) -> str:
    """
    One-line task execution for maximum convenience
    
    Example:
        result = await run_quick_task("Summarize this", data={"text": "..."})
    """
    agent = quick_start()
    await agent.initialize()
    
    result = await agent.run(task, data=data, **kwargs)
    return result.get("output", "")