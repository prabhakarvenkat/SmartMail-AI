from typing import TypedDict, Annotated, List, Optional
from pydantic import BaseModel, Field
import operator

# LangGraph Agent State
class AgentState(TypedDict):
    emails: List[dict] # List of emails to process in the current run
    current_email_index: int
    current_email: Optional[dict]
    classification: Optional[str]
    response_generated: bool
    response_sent: bool

# FastAPI Response Models
class MailProcessResponse(BaseModel):
    message: str
    processed_count: int
    new_emails_fetched: int

class EmailEntry(BaseModel):
    id: int
    message_id: str = Field(..., description="Unique identifier for the email message.")
    subject: str
    sender: str
    body: str
    classification: str
    response_sent: bool
    timestamp: str