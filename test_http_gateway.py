#!/usr/bin/env python3
"""
Test TensorZero gateway with direct HTTP requests.
"""

import requests
import json

def test_gateway():
    """Test TensorZero gateway with HTTP."""
    
    url = "http://localhost:3000/inference"
    
    # Test inference request
    payload = {
        "function_name": "tiny_reasoning",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "What is 2+2?"
                }
            ]
        }
    }
    
    print("Testing TensorZero Gateway HTTP API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Response data:")
            print(json.dumps(data, indent=2))
        else:
            print(f"\n❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

if __name__ == "__main__":
    test_gateway()