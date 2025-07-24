import pytest
from unittest.mock import MagicMock, patch
from app.langgraph_agent import classify_email, AgentState
from app.schemas import AgentState as AgentStateType # Use alias to avoid conflict

# Mock the LLM for testing classification without actual API calls
@pytest.fixture
def mock_llm_invoke():
    """Fixture to mock the LLM's invoke method."""
    with patch('app.langgraph_agent.llm.invoke') as mock_invoke:
        yield mock_invoke

def test_classify_email_important(mock_llm_invoke):
    """Test classification of an 'Important' email."""
    mock_llm_invoke.return_value.content = "Important"
    initial_state: AgentStateType = {
        "emails": [], # Not used in this node
        "current_email_index": 0,
        "current_email": {
            "message_id": "test-1",
            "subject": "Meeting Confirmation",
            "sender": "boss@example.com",
            "body": "Your appointment is confirmed for tomorrow."
        },
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }
    result_state = classify_email(initial_state)
    assert result_state["classification"] == "Important"
    mock_llm_invoke.assert_called_once()

def test_classify_email_spam(mock_llm_invoke):
    """Test classification of a 'SPAM' email."""
    mock_llm_invoke.return_value.content = "SPAM"
    initial_state: AgentStateType = {
        "emails": [],
        "current_email_index": 0,
        "current_email": {
            "message_id": "test-2",
            "subject": "Free V1agra",
            "sender": "spam@scam.net",
            "body": "Click here for amazing offers!"
        },
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }
    result_state = classify_email(initial_state)
    assert result_state["classification"] == "SPAM"
    mock_llm_invoke.assert_called_once()

def test_classify_email_unwanted(mock_llm_invoke):
    """Test classification of an 'Unwanted' email."""
    mock_llm_invoke.return_value.content = "Unwanted"
    initial_state: AgentStateType = {
        "emails": [],
        "current_email_index": 0,
        "current_email": {
            "message_id": "test-3",
            "subject": "Newsletter Update",
            "sender": "marketing@example.com",
            "body": "Our latest product updates."
        },
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }
    result_state = classify_email(initial_state)
    assert result_state["classification"] == "Unwanted"
    mock_llm_invoke.assert_called_once()

def test_classify_email_no_current_email():
    """Test classification when no current email is present."""
    initial_state: AgentStateType = {
        "emails": [],
        "current_email_index": 0,
        "current_email": None, # No email to classify
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }
    result_state = classify_email(initial_state)
    assert result_state["classification"] == "No_Email" # Or a default like "Unclassified"
    # LLM should not be called if there's no email
    # This test doesn't use mock_llm_invoke, so we can't assert on it directly.
    # If LLM was called, it would fail.

def test_classify_email_llm_error(mock_llm_invoke):
    """Test handling of LLM errors during classification."""
    mock_llm_invoke.side_effect = Exception("LLM API error")
    initial_state: AgentStateType = {
        "emails": [],
        "current_email_index": 0,
        "current_email": {
            "message_id": "test-4",
            "subject": "Error Test",
            "sender": "error@example.com",
            "body": "This email should cause an LLM error."
        },
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }
    result_state = classify_email(initial_state)
    assert result_state["classification"] == "Unwanted" # Expect fallback to 'Unwanted'
    mock_llm_invoke.assert_called_once()

def test_classify_email_unexpected_llm_output(mock_llm_invoke):
    """Test handling of unexpected LLM classification output."""
    mock_llm_invoke.return_value.content = "UnexpectedCategory"
    initial_state: AgentStateType = {
        "emails": [],
        "current_email_index": 0,
        "current_email": {
            "message_id": "test-5",
            "subject": "Unexpected Output",
            "sender": "unexpected@example.com",
            "body": "This email's classification should be unexpected."
        },
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }
    result_state = classify_email(initial_state)
    assert result_state["classification"] == "Unwanted" # Expect fallback to 'Unwanted'
    mock_llm_invoke.assert_called_once()