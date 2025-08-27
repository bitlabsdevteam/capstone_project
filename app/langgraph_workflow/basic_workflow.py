"""Basic LangGraph Workflow Implementation

This module demonstrates core LangGraph functionality through a minimal,
self-contained example that showcases fundamental workflow capabilities.

Key Components:
- StateGraph: Main graph class for workflow orchestration
- State: Shared data structure that flows through the workflow
- Nodes: Functions that process and transform state
- Edges: Connections that determine workflow flow
"""

from typing import Dict, List, Any, Optional, TypedDict
try:
    from typing_extensions import Annotated
except ImportError:
    from typing import Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import logging
import json
from datetime import datetime

# Configure logging for workflow tracking
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """State schema for the basic workflow.
    
    This defines the structure of data that flows through the workflow.
    Each field can be updated by nodes and passed to subsequent nodes.
    
    Attributes:
        input_text: Original input text to process
        processed_text: Text after processing transformations
        word_count: Number of words in the processed text
        metadata: Additional information about the processing
        messages: List of messages for tracking workflow progress
        errors: List of any errors encountered during processing
    """
    input_text: str
    processed_text: str
    word_count: int
    metadata: Dict[str, Any]
    messages: Annotated[List[str], add_messages]
    errors: List[str]


class BasicLangGraphWorkflow:
    """A basic LangGraph workflow implementation.
    
    This class demonstrates how to create and execute a simple workflow
    using LangGraph's StateGraph. The workflow processes text through
    multiple stages: validation, processing, analysis, and formatting.
    """
    
    def __init__(self):
        """Initialize the workflow with a compiled StateGraph."""
        self.graph = self._build_workflow()
        logger.info("BasicLangGraphWorkflow initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build and compile the workflow graph.
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create StateGraph with our state schema
        workflow = StateGraph(WorkflowState)
        
        # Add nodes to the workflow
        workflow.add_node("validate_input", self._validate_input_node)
        workflow.add_node("process_text", self._process_text_node)
        workflow.add_node("analyze_content", self._analyze_content_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Define workflow edges (flow control)
        workflow.add_edge(START, "validate_input")
        workflow.add_edge("validate_input", "process_text")
        workflow.add_edge("process_text", "analyze_content")
        workflow.add_edge("analyze_content", "format_output")
        workflow.add_edge("format_output", END)
        
        # Compile the workflow
        compiled_workflow = workflow.compile()
        logger.info("Workflow compiled with 4 nodes and 5 edges")
        
        return compiled_workflow
    
    def _validate_input_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Validate input text and prepare for processing.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with validation results
        """
        logger.info("Executing validate_input_node")
        
        input_text = state.get("input_text", "")
        errors = state.get("errors", [])
        messages = state.get("messages", [])
        
        # Validation logic
        if not input_text or not input_text.strip():
            error_msg = "Input text is empty or contains only whitespace"
            errors.append(error_msg)
            logger.warning(error_msg)
        
        if len(input_text) > 10000:
            error_msg = "Input text exceeds maximum length of 10,000 characters"
            errors.append(error_msg)
            logger.warning(error_msg)
        
        # Update messages
        messages.append(f"Input validation completed at {datetime.now().isoformat()}")
        
        return {
            "input_text": input_text.strip(),
            "messages": messages,
            "errors": errors,
            "metadata": {
                "validation_timestamp": datetime.now().isoformat(),
                "input_length": len(input_text)
            }
        }
    
    def _process_text_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Process and transform the input text.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with processed text
        """
        logger.info("Executing process_text_node")
        
        input_text = state.get("input_text", "")
        messages = state.get("messages", [])
        errors = state.get("errors", [])
        metadata = state.get("metadata", {})
        
        # Skip processing if there are validation errors
        if errors:
            logger.warning("Skipping text processing due to validation errors")
            return {
                "processed_text": "",
                "messages": messages + ["Text processing skipped due to errors"]
            }
        
        try:
            # Basic text processing transformations
            processed_text = input_text.lower()  # Convert to lowercase
            processed_text = processed_text.replace("\n", " ")  # Replace newlines with spaces
            processed_text = " ".join(processed_text.split())  # Normalize whitespace
            
            # Update metadata
            metadata.update({
                "processing_timestamp": datetime.now().isoformat(),
                "transformations_applied": ["lowercase", "normalize_whitespace"]
            })
            
            messages.append(f"Text processing completed: {len(processed_text)} characters")
            logger.info(f"Text processed successfully: {len(processed_text)} characters")
            
            return {
                "processed_text": processed_text,
                "messages": messages,
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"Error during text processing: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return {
                "processed_text": "",
                "messages": messages,
                "errors": errors
            }
    
    def _analyze_content_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Analyze the processed text content.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with analysis results
        """
        logger.info("Executing analyze_content_node")
        
        processed_text = state.get("processed_text", "")
        messages = state.get("messages", [])
        errors = state.get("errors", [])
        metadata = state.get("metadata", {})
        
        # Skip analysis if there are errors or no processed text
        if errors or not processed_text:
            logger.warning("Skipping content analysis due to errors or empty text")
            return {
                "word_count": 0,
                "messages": messages + ["Content analysis skipped"]
            }
        
        try:
            # Perform content analysis
            words = processed_text.split()
            word_count = len(words)
            unique_words = len(set(words))
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Update metadata with analysis results
            metadata.update({
                "analysis_timestamp": datetime.now().isoformat(),
                "unique_words": unique_words,
                "average_word_length": round(avg_word_length, 2),
                "text_complexity": "simple" if avg_word_length < 5 else "complex"
            })
            
            messages.append(f"Content analysis completed: {word_count} words, {unique_words} unique")
            logger.info(f"Analysis completed: {word_count} words analyzed")
            
            return {
                "word_count": word_count,
                "messages": messages,
                "metadata": metadata
            }
            
        except Exception as e:
            error_msg = f"Error during content analysis: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return {
                "word_count": 0,
                "messages": messages,
                "errors": errors
            }
    
    def _format_output_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Format the final output with all processing results.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with formatted output
        """
        logger.info("Executing format_output_node")
        
        messages = state.get("messages", [])
        metadata = state.get("metadata", {})
        
        # Add completion timestamp
        metadata.update({
            "completion_timestamp": datetime.now().isoformat(),
            "workflow_status": "completed" if not state.get("errors") else "completed_with_errors"
        })
        
        messages.append(f"Workflow completed at {datetime.now().isoformat()}")
        logger.info("Output formatting completed")
        
        return {
            "messages": messages,
            "metadata": metadata
        }
    
    def execute(self, input_text: str) -> Dict[str, Any]:
        """Execute the workflow with the given input text.
        
        Args:
            input_text: Text to process through the workflow
            
        Returns:
            Complete workflow state after execution
            
        Raises:
            Exception: If workflow execution fails
        """
        logger.info(f"Starting workflow execution with input length: {len(input_text)}")
        
        try:
            # Initialize state
            initial_state = {
                "input_text": input_text,
                "processed_text": "",
                "word_count": 0,
                "metadata": {},
                "messages": [f"Workflow started at {datetime.now().isoformat()}"],
                "errors": []
            }
            
            # Execute the workflow
            result = self.graph.invoke(initial_state)
            
            logger.info("Workflow execution completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Workflow execution failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg) from e
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about the workflow structure.
        
        Returns:
            Dictionary containing workflow metadata
        """
        return {
            "name": "BasicLangGraphWorkflow",
            "description": "A basic workflow demonstrating LangGraph core functionality",
            "nodes": ["validate_input", "process_text", "analyze_content", "format_output"],
            "state_schema": {
                "input_text": "str",
                "processed_text": "str",
                "word_count": "int",
                "metadata": "Dict[str, Any]",
                "messages": "List[str]",
                "errors": "List[str]"
            },
            "capabilities": [
                "Input validation",
                "Text processing and transformation",
                "Content analysis",
                "Error handling",
                "Progress tracking"
            ]
        }


def create_basic_workflow() -> BasicLangGraphWorkflow:
    """Factory function to create a basic LangGraph workflow.
    
    Returns:
        Initialized BasicLangGraphWorkflow instance
    """
    return BasicLangGraphWorkflow()


# Example usage and demonstration
if __name__ == "__main__":
    # Create workflow instance
    workflow = create_basic_workflow()
    
    # Display workflow information
    print("=== LangGraph Workflow Information ===")
    info = workflow.get_workflow_info()
    print(json.dumps(info, indent=2))
    
    # Example 1: Basic text processing
    print("\n=== Example 1: Basic Text Processing ===")
    sample_text = "Hello World! This is a SAMPLE text for processing.\n\nIt contains multiple lines and UPPERCASE words."
    
    try:
        result = workflow.execute(sample_text)
        print(f"Input: {result['input_text'][:50]}...")
        print(f"Processed: {result['processed_text'][:50]}...")
        print(f"Word Count: {result['word_count']}")
        print(f"Status: {result['metadata'].get('workflow_status', 'unknown')}")
        print(f"Messages: {len(result['messages'])} workflow messages")
        
        if result['errors']:
            print(f"Errors: {result['errors']}")
            
    except Exception as e:
        print(f"Execution failed: {e}")
    
    # Example 2: Error handling with empty input
    print("\n=== Example 2: Error Handling ===")
    try:
        result = workflow.execute("")
        print(f"Status: {result['metadata'].get('workflow_status', 'unknown')}")
        print(f"Errors: {result['errors']}")
        
    except Exception as e:
        print(f"Execution failed: {e}")
    
    print("\n=== Workflow Demonstration Complete ===")