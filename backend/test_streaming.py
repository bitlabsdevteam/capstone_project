#!/usr/bin/env python3
"""Test script for streaming functionality."""

import asyncio
import json
import aiohttp
from datetime import datetime


async def test_streaming_endpoint():
    """Test the streaming workflow execution endpoint."""
    
    # Test data
    test_data = {
        "workflow_name": "supervisor_frontend_workflow",
        "input_data": {
            "user_request": "Create a sales dashboard showing monthly revenue trends",
            "data": {
                "sales_data": [
                    {"month": "Jan", "revenue": 10000},
                    {"month": "Feb", "revenue": 12000},
                    {"month": "Mar", "revenue": 15000}
                ]
            }
        },
        "execution_id": f"test_exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "stream_mode": "values",
        "enable_token_streaming": True
    }
    
    url = "http://localhost:8000/api/v1/supervisor_frontend_workflow/stream"
    
    print(f"Testing streaming endpoint: {url}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    print("\n" + "="*50)
    print("STREAMING RESPONSE:")
    print("="*50)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    print(f"Error: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    return
                
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")
                print("\nStreaming events:")
                
                event_count = 0
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if line_str.startswith('data: '):
                        event_count += 1
                        event_data = line_str[6:]  # Remove 'data: ' prefix
                        
                        try:
                            event = json.loads(event_data)
                            event_type = event.get('type', 'unknown')
                            timestamp = event.get('timestamp', 'no-timestamp')
                            
                            print(f"\n[{event_count}] {event_type} at {timestamp}")
                            
                            # Show different details based on event type
                            if event_type == 'workflow_start':
                                print(f"  Workflow: {event.get('workflow_id')}")
                                print(f"  Execution: {event.get('execution_id')}")
                                
                            elif event_type == 'llm_token':
                                token = event.get('token', '')
                                node = event.get('node', 'unknown')
                                print(f"  Node: {node}")
                                print(f"  Token: '{token}'")
                                
                            elif event_type == 'node_start':
                                node = event.get('node', 'unknown')
                                print(f"  Starting node: {node}")
                                
                            elif event_type == 'node_complete':
                                node = event.get('node', 'unknown')
                                print(f"  Completed node: {node}")
                                
                            elif event_type == 'workflow_complete':
                                print(f"  Workflow completed successfully")
                                
                            elif event_type == 'workflow_error':
                                error = event.get('error', 'Unknown error')
                                print(f"  Error: {error}")
                                
                            else:
                                # Show full event for unknown types
                                print(f"  Data: {json.dumps(event, indent=4)}")
                                
                        except json.JSONDecodeError as e:
                            print(f"  [Invalid JSON] {event_data}")
                            
                    elif line_str:
                        print(f"  [Raw] {line_str}")
                        
                print(f"\n\nTotal events received: {event_count}")
                
    except aiohttp.ClientError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


async def test_streaming_health():
    """Test the streaming health endpoint."""
    
    url = "http://localhost:8000/api/v1/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Streaming health check: {data}")
                    return True
                else:
                    print(f"Health check failed: HTTP {response.status}")
                    return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False


async def main():
    """Main test function."""
    print("Testing LangGraph Async Streaming Implementation")
    print("=" * 50)
    
    # Test health endpoint first
    print("\n1. Testing streaming health endpoint...")
    health_ok = await test_streaming_health()
    
    if not health_ok:
        print("Health check failed. Make sure the server is running.")
        return
    
    print("\n2. Testing streaming workflow execution...")
    await test_streaming_endpoint()
    
    print("\nTest completed!")


if __name__ == "__main__":
    asyncio.run(main())