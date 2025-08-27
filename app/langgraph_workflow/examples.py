"""LangGraph Workflow Examples

This module provides comprehensive examples demonstrating how to use the
BasicLangGraphWorkflow for various text processing scenarios.

Examples include:
- Basic text processing
- Error handling scenarios
- Workflow state inspection
- Custom input validation
- Performance monitoring
"""

import json
import time
from typing import Dict, Any, List
from .basic_workflow import create_basic_workflow


def run_basic_example() -> Dict[str, Any]:
    """Demonstrate basic workflow functionality.
    
    Returns:
        Workflow execution result
    """
    print("\n" + "="*60)
    print("BASIC WORKFLOW EXAMPLE")
    print("="*60)
    
    # Create workflow
    workflow = create_basic_workflow()
    
    # Sample input text
    input_text = """
    Welcome to LangGraph Workflow Demonstration!
    
    This is a SAMPLE text that contains:
    - Multiple lines and paragraphs
    - UPPERCASE and lowercase words
    - Special characters and punctuation!
    - Numbers like 123 and 456
    
    The workflow will process this text through multiple stages:
    validation, processing, analysis, and formatting.
    """
    
    print(f"Input text length: {len(input_text)} characters")
    print(f"Input preview: {input_text[:100]}...")
    
    # Execute workflow
    start_time = time.time()
    result = workflow.execute(input_text)
    execution_time = time.time() - start_time
    
    # Display results
    print(f"\nExecution time: {execution_time:.3f} seconds")
    print(f"Final status: {result['metadata'].get('workflow_status', 'unknown')}")
    print(f"Word count: {result['word_count']}")
    print(f"Unique words: {result['metadata'].get('unique_words', 'N/A')}")
    print(f"Average word length: {result['metadata'].get('average_word_length', 'N/A')}")
    print(f"Text complexity: {result['metadata'].get('text_complexity', 'N/A')}")
    
    print(f"\nProcessed text preview: {result['processed_text'][:100]}...")
    
    print("\nWorkflow messages:")
    for i, message in enumerate(result['messages'], 1):
        print(f"  {i}. {message}")
    
    if result['errors']:
        print("\nErrors encountered:")
        for i, error in enumerate(result['errors'], 1):
            print(f"  {i}. {error}")
    
    return result


def run_error_handling_examples() -> List[Dict[str, Any]]:
    """Demonstrate error handling capabilities.
    
    Returns:
        List of workflow execution results with various error scenarios
    """
    print("\n" + "="*60)
    print("ERROR HANDLING EXAMPLES")
    print("="*60)
    
    workflow = create_basic_workflow()
    results = []
    
    # Test cases with different error scenarios
    test_cases = [
        {
            "name": "Empty Input",
            "input": "",
            "description": "Testing with completely empty input"
        },
        {
            "name": "Whitespace Only",
            "input": "   \n\t   \n   ",
            "description": "Testing with whitespace-only input"
        },
        {
            "name": "Very Long Text",
            "input": "A" * 15000,  # Exceeds 10,000 character limit
            "description": "Testing with text exceeding maximum length"
        },
        {
            "name": "Valid Short Text",
            "input": "This is a valid short text for processing.",
            "description": "Testing with valid input for comparison"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        print(f"Description: {test_case['description']}")
        print(f"Input length: {len(test_case['input'])} characters")
        
        try:
            result = workflow.execute(test_case['input'])
            
            print(f"Status: {result['metadata'].get('workflow_status', 'unknown')}")
            print(f"Word count: {result['word_count']}")
            
            if result['errors']:
                print(f"Errors ({len(result['errors'])}):")
                for error in result['errors']:
                    print(f"  - {error}")
            else:
                print("No errors encountered")
            
            results.append({
                "test_case": test_case['name'],
                "success": True,
                "result": result
            })
            
        except Exception as e:
            print(f"Execution failed: {e}")
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    return results


def run_workflow_inspection_example() -> Dict[str, Any]:
    """Demonstrate workflow inspection and metadata analysis.
    
    Returns:
        Workflow information and analysis
    """
    print("\n" + "="*60)
    print("WORKFLOW INSPECTION EXAMPLE")
    print("="*60)
    
    workflow = create_basic_workflow()
    
    # Get workflow information
    workflow_info = workflow.get_workflow_info()
    
    print("Workflow Information:")
    print(json.dumps(workflow_info, indent=2))
    
    # Execute a sample workflow to analyze state transitions
    sample_text = "LangGraph enables powerful workflow orchestration with state management."
    result = workflow.execute(sample_text)
    
    print("\nState Analysis:")
    print(f"Initial input length: {len(result['input_text'])}")
    print(f"Processed text length: {len(result['processed_text'])}")
    print(f"Total messages: {len(result['messages'])}")
    print(f"Processing stages: {len(workflow_info['nodes'])}")
    
    # Analyze metadata timeline
    metadata = result['metadata']
    timestamps = [
        ('validation', metadata.get('validation_timestamp')),
        ('processing', metadata.get('processing_timestamp')),
        ('analysis', metadata.get('analysis_timestamp')),
        ('completion', metadata.get('completion_timestamp'))
    ]
    
    print("\nProcessing Timeline:")
    for stage, timestamp in timestamps:
        if timestamp:
            print(f"  {stage.capitalize()}: {timestamp}")
    
    return {
        "workflow_info": workflow_info,
        "execution_result": result,
        "analysis": {
            "total_processing_stages": len(workflow_info['nodes']),
            "state_fields": len(workflow_info['state_schema']),
            "capabilities": len(workflow_info['capabilities'])
        }
    }


def run_performance_benchmark() -> Dict[str, Any]:
    """Benchmark workflow performance with different input sizes.
    
    Returns:
        Performance analysis results
    """
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    workflow = create_basic_workflow()
    
    # Test with different input sizes
    test_sizes = [100, 500, 1000, 2000, 5000]
    benchmark_results = []
    
    for size in test_sizes:
        # Generate test text of specified size
        test_text = " ".join([f"word{i}" for i in range(size // 5)])  # Approximate word count
        
        print(f"\nTesting with ~{size} characters ({len(test_text)} actual)...")
        
        # Measure execution time
        start_time = time.time()
        result = workflow.execute(test_text)
        execution_time = time.time() - start_time
        
        benchmark_result = {
            "input_size": len(test_text),
            "word_count": result['word_count'],
            "execution_time": execution_time,
            "words_per_second": result['word_count'] / execution_time if execution_time > 0 else 0,
            "status": result['metadata'].get('workflow_status', 'unknown')
        }
        
        benchmark_results.append(benchmark_result)
        
        print(f"  Execution time: {execution_time:.3f}s")
        print(f"  Words processed: {result['word_count']}")
        print(f"  Processing rate: {benchmark_result['words_per_second']:.1f} words/second")
    
    # Calculate performance statistics
    avg_execution_time = sum(r['execution_time'] for r in benchmark_results) / len(benchmark_results)
    avg_processing_rate = sum(r['words_per_second'] for r in benchmark_results) / len(benchmark_results)
    
    performance_summary = {
        "benchmark_results": benchmark_results,
        "statistics": {
            "average_execution_time": avg_execution_time,
            "average_processing_rate": avg_processing_rate,
            "total_tests": len(benchmark_results)
        }
    }
    
    print(f"\nPerformance Summary:")
    print(f"  Average execution time: {avg_execution_time:.3f}s")
    print(f"  Average processing rate: {avg_processing_rate:.1f} words/second")
    print(f"  Total tests completed: {len(benchmark_results)}")
    
    return performance_summary


def run_all_examples() -> Dict[str, Any]:
    """Run all workflow examples and return comprehensive results.
    
    Returns:
        Dictionary containing all example results
    """
    print("\n" + "="*80)
    print("LANGGRAPH WORKFLOW - COMPREHENSIVE EXAMPLES")
    print("="*80)
    
    all_results = {}
    
    try:
        # Run basic example
        all_results['basic_example'] = run_basic_example()
        
        # Run error handling examples
        all_results['error_handling'] = run_error_handling_examples()
        
        # Run workflow inspection
        all_results['workflow_inspection'] = run_workflow_inspection_example()
        
        # Run performance benchmark
        all_results['performance_benchmark'] = run_performance_benchmark()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        all_results['error'] = str(e)
    
    return all_results


if __name__ == "__main__":
    # Run all examples when script is executed directly
    results = run_all_examples()
    
    # Optionally save results to file
    try:
        with open('workflow_examples_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("\nResults saved to 'workflow_examples_results.json'")
    except Exception as e:
        print(f"\nCould not save results to file: {e}")