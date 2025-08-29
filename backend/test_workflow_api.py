#!/usr/bin/env python3
"""
Test script for Workflow API endpoints.

This script tests the workflow API endpoints using Docker Compose.
It verifies that the API is accessible and responds correctly to standard requests,
validates workflow execution, checks error handling, and confirms successful workflow steps.
"""

import asyncio
import json
import aiohttp
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
WORKFLOW_API_URL = f"{BASE_URL}/workflows"
HEALTH_API_URL = f"{BASE_URL}/health"

# Test data
TEST_WORKFLOW = {
    "name": "test_workflow",
    "workflow_type": "supervisor_frontend_workflow",
    "description": "Test workflow for API testing",
    "config": {
        "max_steps": 10,
        "timeout_seconds": 60
    }
}

TEST_EXECUTION = {
    "input_data": {
        "user_request": "Create a simple hello world application",
        "data": {}
    },
    "execution_mode": "sync",
    "timeout_seconds": 120
}

# Test results tracking
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "details": []
}


def log_test_result(test_name: str, passed: bool, details: str = "") -> None:
    """Log test result and update test_results dictionary"""
    result = "PASSED" if passed else "FAILED"
    print(f"[{result}] {test_name}")
    if details:
        print(f"  Details: {details}")
    
    test_results["total"] += 1
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
    
    test_results["details"].append({
        "test_name": test_name,
        "result": result,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })


async def wait_for_service_ready(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """Wait for the API service to be ready"""
    print(f"Waiting for API service to be ready at {HEALTH_API_URL}...")
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(HEALTH_API_URL) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        if health_data.get("status") == "healthy":
                            print(f"API service is ready after {attempt + 1} attempts")
                            return True
                        print(f"API service health check returned status: {health_data.get('status')}")
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: Service not ready yet. Error: {str(e)}")
        
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_interval} seconds...")
            await asyncio.sleep(retry_interval)
    
    print(f"API service failed to become ready after {max_retries} attempts")
    return False


async def test_health_endpoint() -> bool:
    """Test the health endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(HEALTH_API_URL) as response:
                if response.status != 200:
                    log_test_result("Health Endpoint", False, f"Expected status 200, got {response.status}")
                    return False
                
                health_data = await response.json()
                if health_data.get("status") != "healthy":
                    log_test_result("Health Endpoint", False, 
                                   f"Expected status 'healthy', got '{health_data.get('status')}'. Details: {json.dumps(health_data)}")
                    return False
                
                log_test_result("Health Endpoint", True, "Health endpoint returned healthy status")
                return True
    except Exception as e:
        log_test_result("Health Endpoint", False, f"Exception: {str(e)}")
        return False


async def test_list_workflows() -> bool:
    """Test listing workflows"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WORKFLOW_API_URL) as response:
                if response.status != 200:
                    log_test_result("List Workflows", False, f"Expected status 200, got {response.status}")
                    return False
                
                data = await response.json()
                if "workflows" not in data:
                    log_test_result("List Workflows", False, "Response missing 'workflows' key")
                    return False
                
                log_test_result("List Workflows", True, f"Found {len(data['workflows'])} workflows")
                return True
    except Exception as e:
        log_test_result("List Workflows", False, f"Exception: {str(e)}")
        return False


async def test_create_workflow() -> Optional[str]:
    """Test creating a workflow"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                WORKFLOW_API_URL,
                json=TEST_WORKFLOW,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_text = await response.text()
                
                if response.status != 201:
                    log_test_result("Create Workflow", False, 
                                   f"Expected status 201, got {response.status}. Response: {response_text}")
                    return None
                
                data = json.loads(response_text)
                if "id" not in data:
                    log_test_result("Create Workflow", False, "Response missing 'id' key")
                    return None
                
                workflow_id = data["id"]
                log_test_result("Create Workflow", True, f"Created workflow with ID: {workflow_id}")
                return workflow_id
    except Exception as e:
        log_test_result("Create Workflow", False, f"Exception: {str(e)}")
        return None


async def test_get_workflow(workflow_name: str) -> bool:
    """Test getting a specific workflow"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{WORKFLOW_API_URL}/{workflow_name}") as response:
                if response.status != 200:
                    log_test_result("Get Workflow", False, f"Expected status 200, got {response.status}")
                    return False
                
                data = await response.json()
                if data.get("name") != workflow_name:
                    log_test_result("Get Workflow", False, 
                                   f"Expected workflow name '{workflow_name}', got '{data.get('name')}")
                    return False
                
                log_test_result("Get Workflow", True, f"Successfully retrieved workflow: {workflow_name}")
                return True
    except Exception as e:
        log_test_result("Get Workflow", False, f"Exception: {str(e)}")
        return False


async def test_execute_workflow(workflow_name: str) -> Optional[str]:
    """Test executing a workflow"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WORKFLOW_API_URL}/{workflow_name}/execute",
                json=TEST_EXECUTION,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    log_test_result("Execute Workflow", False, 
                                   f"Expected status 200, got {response.status}. Response: {response_text}")
                    return None
                
                data = await response.json()
                if "id" not in data:
                    log_test_result("Execute Workflow", False, "Response missing 'id' key")
                    return None
                
                execution_id = data["id"]
                status = data.get("status", "unknown")
                log_test_result("Execute Workflow", True, 
                               f"Started execution with ID: {execution_id}, status: {status}")
                return execution_id
    except Exception as e:
        log_test_result("Execute Workflow", False, f"Exception: {str(e)}")
        return None


async def test_invalid_workflow_execution() -> bool:
    """Test executing a non-existent workflow"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WORKFLOW_API_URL}/non_existent_workflow/execute",
                json=TEST_EXECUTION,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 404:
                    log_test_result("Invalid Workflow Execution", True, 
                                   "Correctly returned 404 for non-existent workflow")
                    return True
                else:
                    log_test_result("Invalid Workflow Execution", False, 
                                   f"Expected status 404, got {response.status}")
                    return False
    except Exception as e:
        log_test_result("Invalid Workflow Execution", False, f"Exception: {str(e)}")
        return False


async def test_invalid_input_data() -> bool:
    """Test executing a workflow with invalid input data"""
    try:
        # First, get a valid workflow name
        async with aiohttp.ClientSession() as session:
            async with session.get(WORKFLOW_API_URL) as response:
                if response.status != 200:
                    log_test_result("Invalid Input Data", False, "Could not get workflow list")
                    return False
                
                data = await response.json()
                if not data.get("workflows"):
                    log_test_result("Invalid Input Data", False, "No workflows found")
                    return False
                
                workflow_name = data["workflows"][0]["name"]
        
        # Now test with invalid input
        invalid_data = {"input_data": "not_a_valid_object", "execution_mode": "invalid"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{WORKFLOW_API_URL}/{workflow_name}/execute",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [400, 422]:
                    log_test_result("Invalid Input Data", True, 
                                   f"Correctly returned {response.status} for invalid input data")
                    return True
                else:
                    log_test_result("Invalid Input Data", False, 
                                   f"Expected status 400 or 422, got {response.status}")
                    return False
    except Exception as e:
        log_test_result("Invalid Input Data", False, f"Exception: {str(e)}")
        return False


async def run_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("WORKFLOW API TESTS")
    print("="*50)
    
    # Wait for service to be ready
    service_ready = await wait_for_service_ready()
    if not service_ready:
        print("\nCould not connect to API service. Tests aborted.")
        return
    
    # Run tests
    await test_health_endpoint()
    await test_list_workflows()
    
    # Create a workflow and test operations on it
    workflow_name = TEST_WORKFLOW["name"]
    created_workflow_id = await test_create_workflow()
    
    if created_workflow_id:
        await test_get_workflow(workflow_name)
        await test_execute_workflow(workflow_name)
    
    # Test error handling
    await test_invalid_workflow_execution()
    await test_invalid_input_data()
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Skipped: {test_results['skipped']}")
    print("="*50)
    
    # Return non-zero exit code if any tests failed
    if test_results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())