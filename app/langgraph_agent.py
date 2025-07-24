from typing import List
from langchain_groq import ChatGroq # Changed from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

from app.schemas import AgentState
from app.email_client import send_email_reply
from app.database import store_email_data, get_email_by_message_id
from app.config import settings
import re

# Initialize the LLM with the API key from settings
# Changed ChatOpenAI to ChatGroq and parameter from openai_api_key to groq_api_key
llm = ChatGroq(model="llama3-8b-8192", temperature=0, groq_api_key=settings.GROQ_API_KEY) # You can choose other Groq models like 'mixtral-8x7b-32768' or 'llama3-70b-8192'

# --- Nodes for the LangGraph Workflow ---

def fetch_and_set_email(state: AgentState) -> AgentState:
    """
    Fetches the next email from the batch and sets it as the current_email in the state.
    If no more emails, sets current_email to None and signals end.
    """
    emails = state.get("emails", [])
    current_index = state.get("current_email_index", 0)

    if current_index < len(emails):
        current_email = emails[current_index]
        print(f"Processing email {current_index + 1}/{len(emails)}: '{current_email['subject']}'")
        return {
            "current_email": current_email,
            "current_email_index": current_index + 1, # Increment for the next iteration
            "classification": None,
            "response_generated": False,
            "response_sent": False
        }
    else:
        print("No more emails to process in this batch.")
        return {
            "current_email": None, # Signal no more emails
            "current_email_index": current_index,
            "classification": None,
            "response_generated": False,
            "response_sent": False
        }

def classify_email(state: AgentState) -> AgentState:
    """
    Uses the LLM to classify the current email into SPAM, Unwanted, or Important.
    """
    current_email = state["current_email"]
    if not current_email:
        # This case should ideally be caught by the conditional edge before this node
        print("No current email to classify.")
        return {"classification": "No_Email"}

    subject = current_email.get("subject", "")
    body = current_email.get("body", "")

    prompt = f"""
    Please classify the following email into one of these three categories:
    - SPAM
    - Unwanted (non-spam but irrelevant)
    - Important for Business

    Email Subject: {subject}
    Email Body: {body}

    Your classification should be a single word: SPAM, Unwanted, or Important.
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        classification = response.content.strip()
        # Basic sanitization/validation of LLM output
        if classification not in ["SPAM", "Unwanted", "Important"]:
            print(f"LLM returned unexpected classification: '{classification}'. Defaulting to Unwanted.")
            classification = "Unwanted" # Fallback for unexpected LLM output
        print(f"Email Classified: '{classification}' for subject: '{subject}'")
        return {"classification": classification}
    except Exception as e:
        print(f"Error classifying email with LLM: {e}. Defaulting to Unwanted.")
        return {"classification": "Unwanted"} # Handle LLM errors gracefully

def generate_response(state: AgentState) -> AgentState:
    """
    Generates a fixed response for 'Important for Business' emails.
    In a more advanced system, this would use an LLM for dynamic content.
    """
    classification = state["classification"]
    if classification == "Important":
        print("Response generation triggered for 'Important' email.")
        # As per requirements, fixed response
        return {
            "response_generated": True
        }
    return {"response_generated": False} # Should not be reached if routing is correct

def send_email_response(state: AgentState) -> AgentState:
    """
    Sends the generated email reply. Includes a check to prevent duplicate sends.
    """
    current_email = state["current_email"]
    response_generated = state["response_generated"]

    if response_generated and current_email:
        sender_email_raw = current_email["sender"]
        # Extract just the email address from formats like "Name <email@example.com>"
        match = re.search(r'<([^>]+)>', sender_email_raw)
        to_address = match.group(1) if match else sender_email_raw

        subject = "Appointment Confirmed"
        body = "Thank you for your email. Your request has been noted, and the appointment has been fixed. Looking forward to connecting with you."

        # Check if a reply has already been sent for this message_id
        # This acts as a simple rate-limiting/duplicate avoidance mechanism
        message_id = current_email.get("message_id")
        db_email_data = get_email_by_message_id(message_id)
        if db_email_data and db_email_data[6]: # Assuming index 6 is response_sent (boolean)
            print(f"Reply already sent for message ID: '{message_id}'. Skipping send.")
            return {"response_sent": True} # Mark as sent even if skipped to update DB

        success = send_email_reply(to_address, subject, body)
        return {"response_sent": success}
    print("No response generated or no current email to send reply for.")
    return {"response_sent": False}

def store_email_data_node(state: AgentState) -> AgentState:
    """
    Stores the current email's details, classification, and response status in the database.
    """
    current_email = state["current_email"]
    classification = state["classification"]
    response_sent = state["response_sent"]

    if current_email:
        message_id = current_email.get("message_id")
        subject = current_email.get("subject")
        sender = current_email.get("sender")
        body = current_email.get("body")
        # Ensure classification is not None before storing
        final_classification = classification if classification else "Unclassified"
        store_email_data(message_id, subject, sender, body, final_classification, response_sent)
        print(f"Email '{subject}' (ID: {message_id}) stored with classification '{final_classification}' and response_sent={response_sent}")
    else:
        print("No current email data to store.")
    return {} # No state change needed after storing, just side effect

# --- Conditional Edges (Routing Logic) ---

def should_continue_processing(state: AgentState) -> str:
    """
    Determines if there are more emails in the batch to process.
    """
    if state["current_email"] is None:
        return "end_batch"
    return "process_email"

def route_classification(state: AgentState) -> str:
    """
    Routes the workflow based on the email's classification.
    """
    if state["classification"] == "Important":
        return "generate_response"
    elif state["classification"] in ["SPAM", "Unwanted"]:
        return "store_email"
    else: # Fallback for unexpected classifications
        print(f"Unexpected classification: {state['classification']}. Routing to store.")
        return "store_email"

def route_after_response(state: AgentState) -> str:
    """
    Determines if there are more emails to process after storing the current one.
    """
    emails = state.get("emails", [])
    current_index = state.get("current_email_index", 0) # This is already incremented for the NEXT email

    if current_index < len(emails):
        return "next_email"
    else:
        return "end_batch"

# --- Build the LangGraph Workflow ---

workflow = StateGraph(AgentState)

# Add nodes to the workflow
workflow.add_node("fetch_and_set_email", fetch_and_set_email)
workflow.add_node("classify_email", classify_email)
workflow.add_node("generate_response", generate_response)
workflow.add_node("send_email_response", send_email_response)
workflow.add_node("store_email_data", store_email_data_node)

# Set the entry point for the graph
workflow.set_entry_point("fetch_and_set_email")

# Define the edges (transitions) between nodes
workflow.add_conditional_edges(
    "fetch_and_set_email",
    should_continue_processing,
    {
        "process_email": "classify_email", # If there's an email, classify it
        "end_batch": END                     # If no more emails, end the graph run
    }
)

workflow.add_conditional_edges(
    "classify_email",
    route_classification,
    {
        "generate_response": "generate_response", # If Important, generate response
        "store_email": "store_email_data"         # If SPAM/Unwanted, just store
    }
)

workflow.add_edge("generate_response", "send_email_response") # After generating, send the response
workflow.add_edge("send_email_response", "store_email_data") # After sending (or skipping), store the data

# After storing data, decide whether to process the next email or end the batch
workflow.add_conditional_edges(
    "store_email_data",
    route_after_response,
    {
        "next_email": "fetch_and_set_email", # Loop back to fetch the next email in the batch
        "end_batch": END                     # If no more emails in the batch, end
    }
)

# Compile the workflow into a runnable agent
app_agent = workflow.compile()

if __name__ == "__main__":
    # This block is for direct testing of the agent workflow
    print("--- LangGraph Agent Test ---")
    from app.email_client import fetch_unseen_emails
    from app.database import init_db, get_all_emails

    init_db() # Ensure DB is initialized for testing

    print("Fetching unseen emails for agent test run...")
    unseen_emails = fetch_unseen_emails()

    if unseen_emails:
        print(f"Starting agent to process {len(unseen_emails)} emails...")
        initial_state = {
            "emails": unseen_emails,
            "current_email_index": 0,
            "current_email": None, # Will be set by fetch_and_set_email
            "classification": None,
            "response_generated": False,
            "response_sent": False
        }
        # Stream the execution to see intermediate steps
        for s in app_agent.stream(initial_state):
            print(s)
            print("-" * 20)
        print("Agent processing complete.")
    else:
        print("No unseen emails to process for this test run.")

    print("\n--- All Emails in DB After Agent Test ---")
    for email_entry in get_all_emails():
        print(email_entry)
    print("--- LangGraph Agent Test Complete ---")