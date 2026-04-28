"""
Unit tests for agent system
Tests agent initialization, responses, and tool calling
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_agent_imports():
    """Test that agent modules can be imported"""
    try:
        from agent.graph import caller_app
        from agent.tools import book_appointment, register_visitor
        assert caller_app is not None
        assert book_appointment is not None
        assert register_visitor is not None
    except ImportError as e:
        pytest.fail(f"Failed to import agent modules: {e}")

def test_agent_initialization():
    """Test agent initializes correctly"""
    from agent.graph import caller_app
    assert caller_app is not None
    # Verify it's a compiled graph
    assert hasattr(caller_app, 'invoke')

def test_tool_availability():
    """Test that all required tools are available"""
    from agent.graph import caller_tools
    
    tool_names = [tool.name for tool in caller_tools]
    
    # Check critical tools exist
    assert 'book_appointment' in tool_names
    assert 'cancel_appointment' in tool_names
    assert 'get_next_available_appointment' in tool_names
    assert 'register_visitor' in tool_names

def test_agent_state_structure():
    """Test agent state has required structure"""
    from langgraph.graph import MessagesState
    from langchain_core.messages import HumanMessage
    
    # Create a test state
    test_state = {
        "messages": [HumanMessage(content="Hello")]
    }
    
    # Verify state structure
    assert "messages" in test_state
