#!/usr/bin/env python3
"""
Simple test script to verify TensorZero is working.
"""

import asyncio
import os
from tensorzero import AsyncTensorZeroGateway

async def test_tensorzero():
    """Test basic TensorZero functionality."""
    
    print("Testing TensorZero Gateway...")
    print(f"OPENAI_API_KEY set: {bool(os.getenv('OPENAI_API_KEY'))}")
    
    try:
        # Test HTTP gateway connection
        gateway_url = "http://localhost:3000"
        print(f"\n1. Connecting to HTTP gateway at {gateway_url}...")
        
        gateway = await AsyncTensorZeroGateway.build_http(
            gateway_url=gateway_url
        )
        print("   ✓ Connected to HTTP gateway")
        
        # Test a simple inference
        print("\n2. Testing inference with tiny_reasoning function...")
        
        response = await gateway.inference(
            function_name="tiny_reasoning",
            input={
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message: What is 2+2?"
                    }
                ]
            }
        )
        
        print("   ✓ Inference successful!")
        print(f"   Response type: {type(response)}")
        print(f"   Response: {response}")
        
        # Extract content
        if hasattr(response, 'content'):
            print(f"\n3. Content extraction:")
            print(f"   Content type: {type(response.content)}")
            if response.content:
                for i, block in enumerate(response.content):
                    print(f"   Block {i}: {block}")
                    if hasattr(block, 'text'):
                        print(f"   Text: {block.text}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tensorzero())