from fastapi import FastAPI, HTTPException, Depends, status, Header 
from typing import List, Optional, Annotated 

from app.schemas import MailProcessResponse, EmailEntry
from app.langgraph_agent import app_agent, AgentState
from app.email_client import fetch_unseen_emails
from app.database import init_db, get_all_emails, store_email_data
from app.config import settings

app = FastAPI(
    title="SmartMail AI Agent",
    description="An AI agent to classify and respond to emails using LangGraph and FastAPI.",
    version="1.0.0"
)

# Initialize the database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("Database initialized on startup.")

# --- API Key Authentication ---
# Removed: api_key_header = APIKeyHeader(name="X-API-Key")

def get_api_key(x_api_key: Annotated[str, Header(alias="X-API-Key")]): 
    """
    Dependency to validate the API Key.
    Raises HTTPException if the key is invalid.
    """
    if x_api_key == settings.API_KEY:
        return x_api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

# --- Endpoints ---

@app.post("/check-mails", response_model=MailProcessResponse, summary="Trigger email processing")
async def check_mails(api_key_dep: str = Depends(get_api_key)): 
    """
    Fetches unseen emails, classifies them using the LangGraph agent,
    and sends automatic replies for 'Important for Business' emails.
    """
    print("API call received: POST /check-mails")
    unseen_emails = fetch_unseen_emails()
    if not unseen_emails:
        print("No new unseen emails to process.")
        return MailProcessResponse(
            message="No new unseen emails to process.",
            processed_count=0,
            new_emails_fetched=0
        )

    initial_state = {
        "emails": unseen_emails,
        "current_email_index": 0,
        "current_email": None,
        "classification": None,
        "response_generated": False,
        "response_sent": False
    }

    processed_count = 0
    try:
        for s in app_agent.stream(initial_state):
            pass
        processed_count = len(unseen_emails)
        print(f"Finished processing {processed_count} emails.")
        return MailProcessResponse(
            message="Email processing initiated successfully.",
            processed_count=processed_count,
            new_emails_fetched=len(unseen_emails)
        )
    except Exception as e:
        print(f"An error occurred during email processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during email processing: {e}"
        )

@app.get("/dashboard", response_model=List[EmailEntry], summary="View classified emails dashboard")
async def dashboard(api_key_dep: str = Depends(get_api_key)): 
    """
    Returns a list of all classified emails stored in the database,
    ordered by most recent.
    """
    print("API call received: GET /dashboard")
    emails_data = get_all_emails()
    formatted_emails = []
    for email_tuple in emails_data:
        formatted_emails.append(EmailEntry(
            id=email_tuple[0],
            message_id=email_tuple[1],
            subject=email_tuple[2],
            sender=email_tuple[3],
            body=email_tuple[4],
            classification=email_tuple[5],
            response_sent=bool(email_tuple[6]),
            timestamp=email_tuple[7]
        ))
    print(f"Returning {len(formatted_emails)} classified emails for dashboard.")
    return formatted_emails

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to SmartMail AI Agent. Go to /docs for API documentation."}