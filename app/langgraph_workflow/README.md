# LangGraph Workflow Implementation

A basic, self-contained LangGraph workflow implementation that demonstrates core functionality through minimal examples. This implementation showcases fundamental LangGraph concepts while maintaining clean, readable code suitable for educational purposes and as a foundation for extension.

## Overview

This module provides a complete LangGraph workflow implementation that processes text through multiple stages: validation, processing, analysis, and formatting. The workflow demonstrates key LangGraph concepts including state management, node orchestration, and error handling.

## Architecture

### Core Components

1. **WorkflowState**: TypedDict defining the shared state structure
2. **BasicLangGraphWorkflow**: Main workflow class containing all processing nodes
3. **StateGraph**: LangGraph's graph structure for workflow orchestration
4. **Nodes**: Individual processing functions that transform the state
5. **Edges**: Connections between nodes defining the execution flow

### Workflow Structure

```
START → validate_input → process_text → analyze_content → format_output → END
```

## Key Features

- **State Management**: Centralized state using TypedDict for type safety
- **Error Handling**: Comprehensive error collection and validation
- **Metadata Tracking**: Detailed processing information and timestamps
- **Modular Design**: Clean separation of concerns across processing stages
- **Performance Monitoring**: Built-in timing and analysis capabilities
- **Extensible Architecture**: Easy to add new nodes and processing stages

## Installation & Setup

Ensure you have LangGraph installed:

```bash
pip install langgraph
```

## Usage

### Basic Usage

```python
from app.langgraph_workflow import create_basic_workflow

# Create workflow instance
workflow = create_basic_workflow()

# Execute workflow
result = workflow.execute("Your text to process here")

# Access results
print(f"Processed text: {result['processed_text']}")
print(f"Word count: {result['word_count']}")
print(f"Status: {result['metadata']['workflow_status']}")
```

### Advanced Usage

```python
from app.langgraph_workflow import BasicLangGraphWorkflow, WorkflowState

# Create workflow with custom configuration
workflow = BasicLangGraphWorkflow()

# Get workflow information
info = workflow.get_workflow_info()
print(f"Available nodes: {info['nodes']}")
print(f"Capabilities: {info['capabilities']}")

# Execute with error handling
try:
    result = workflow.execute("Sample text")
    if result['errors']:
        print(f"Warnings: {result['errors']}")
except Exception as e:
    print(f"Execution failed: {e}")
```

## State Schema

The `WorkflowState` defines the shared data structure:

```python
class WorkflowState(TypedDict):
    # Input/Output
    input_text: str
    processed_text: str
    
    # Analysis Results
    word_count: int
    character_count: int
    
    # Processing Information
    messages: List[str]
    errors: List[str]
    metadata: Dict[str, Any]
```

## Processing Nodes

### 1. Input Validation (`validate_input`)
- Validates input text length and content
- Checks for empty or whitespace-only input
- Enforces maximum length limits (10,000 characters)
- Records validation timestamps and messages

### 2. Text Processing (`process_text`)
- Normalizes whitespace and formatting
- Converts text to lowercase for analysis
- Removes extra spaces and line breaks
- Tracks processing statistics

### 3. Content Analysis (`analyze_content`)
- Counts words and characters
- Calculates text complexity metrics
- Identifies unique words and patterns
- Generates analysis metadata

### 4. Output Formatting (`format_output`)
- Formats final output structure
- Adds completion timestamps
- Consolidates all processing information
- Prepares final state for return

## Error Handling

The workflow implements comprehensive error handling:

- **Input Validation Errors**: Empty input, excessive length
- **Processing Errors**: Text processing failures
- **State Errors**: Invalid state transitions
- **Runtime Errors**: Unexpected execution issues

Errors are collected in the `errors` list and don't stop execution unless critical.

## Examples

Run the comprehensive examples:

```python
from app.langgraph_workflow.examples import run_all_examples

# Run all demonstration examples
results = run_all_examples()
```

Available example functions:
- `run_basic_example()`: Basic workflow demonstration
- `run_error_handling_examples()`: Error scenarios
- `run_workflow_inspection_example()`: Workflow analysis
- `run_performance_benchmark()`: Performance testing

## Extending the Workflow

### Adding New Nodes

```python
def custom_processing_node(state: WorkflowState) -> WorkflowState:
    """Custom processing node example."""
    # Your custom logic here
    state["messages"].append("Custom processing completed")
    return state

# Add to workflow
workflow.graph.add_node("custom_process", custom_processing_node)
workflow.graph.add_edge("process_text", "custom_process")
workflow.graph.add_edge("custom_process", "analyze_content")
```

### Modifying State Schema

```python
class ExtendedWorkflowState(WorkflowState):
    custom_field: str
    additional_data: Dict[str, Any]
```

### Custom Workflow Creation

```python
from langgraph.graph import StateGraph

def create_custom_workflow():
    graph = StateGraph(ExtendedWorkflowState)
    # Add your custom nodes and edges
    return graph.compile()
```

## Best Practices

1. **State Immutability**: Always return modified state, don't mutate in place
2. **Error Collection**: Use the errors list for non-critical issues
3. **Metadata Usage**: Store processing information in metadata
4. **Type Safety**: Use TypedDict for state schema definition
5. **Node Isolation**: Keep nodes focused on single responsibilities
6. **Edge Management**: Clearly define node execution order

## Performance Considerations

- **Input Size**: Workflow handles up to 10,000 characters efficiently
- **Processing Speed**: ~1000-5000 words per second on typical hardware
- **Memory Usage**: Minimal memory footprint with state-based processing
- **Scalability**: Linear performance scaling with input size

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure LangGraph is properly installed
2. **State Errors**: Verify state schema matches node expectations
3. **Execution Failures**: Check input validation requirements
4. **Performance Issues**: Monitor input size and complexity

### Debug Mode

```python
# Enable detailed logging
result = workflow.execute(text)
for message in result['messages']:
    print(f"DEBUG: {message}")
```

## API Reference

### BasicLangGraphWorkflow

#### Methods

- `execute(text: str) -> WorkflowState`: Execute workflow with input text
- `get_workflow_info() -> Dict[str, Any]`: Get workflow metadata

#### Properties

- `graph`: The compiled LangGraph StateGraph instance

### Factory Functions

- `create_basic_workflow() -> BasicLangGraphWorkflow`: Create workflow instance

## Contributing

When extending this workflow:

1. Follow the existing code style and patterns
2. Add comprehensive error handling
3. Include type hints and documentation
4. Test with various input scenarios
5. Update this README with new features

## License

This implementation is part of the Vizuara Capstone Project.

---

*This LangGraph workflow implementation demonstrates core concepts while maintaining simplicity and extensibility. It serves as both an educational resource and a foundation for building more complex workflow systems.*