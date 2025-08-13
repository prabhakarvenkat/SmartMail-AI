# SmartMail AI Agent

This project implements an Agentic AI system using Python, LangGraph, and FastAPI to automate email classification and response generation.

## Features

- **Email Fetching:** Connects to an IMAP mailbox to retrieve unseen emails.
- **AI Classification:** Utilizes an LLM (**Groq**/GPT-based) to classify emails into: # Changed line 1
    - SPAM
    - Unwanted (non-spam but irrelevant)
    - Important for Business
- **Automated Replies:** Automatically generates and sends professional replies for emails classified as "Important for Business".
- **FastAPI Interface:** Exposes the functionality via a RESTful API (`/check-mails` to trigger processing, `/dashboard` to view results).
- **Data Storage:** Stores email details, classification, and response status in a local SQLite database for auditing.
- **API Authentication:** Basic token-based authentication for API endpoints.
- **Duplicate Prevention:** Simple mechanism to avoid sending duplicate replies to the same email.

## Project Structure

```

smartmail\_ai/
├── app/
│   ├── **init**.py             \# Initializes the app package
│   ├── main.py                 \# FastAPI application with routes
│   ├── config.py               \# Handles configuration and environment variables
│   ├── schemas.py              \# Pydantic models for data validation and API responses
│   ├── email\_client.py         \# IMAP/SMTP logic for email communication
│   ├── langgraph\_agent.py      \# LangGraph workflow for email classification and response
│   ├── utils.py                \# Placeholder for general utility functions
│   └── database.py             \# SQLite database operations
│
├── tests/
│   ├── **init**.py
│   └── test\_classification.py  \# Placeholder for tests
│
├── .env                        \# Environment variables (secrets)
├── requirements.txt            \# Python dependencies
├── README.md                   \# Project description and setup instructions
└── run.py                      \# Entry point to run the FastAPI application

````

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd smartmail_ai
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory (`smartmail_ai/.env`) and populate it with your credentials:

    ```dotenv
    GROQ_API_KEY="your_groq_api_key" # Changed from OPENAI_API_KEY
    IMAP_SERVER="imap.gmail.com"
    IMAP_PORT="993"
    SMTP_SERVER="smtp.gmail.com"
    SMTP_PORT="587"
    EMAIL_ADDRESS="your_gmail_email@gmail.com"
    EMAIL_APP_PASSWORD="your_gmail_app_password" # IMPORTANT: Use an App Password for Gmail
    API_KEY="your_super_secret_api_key"
    ```
    * **Gmail App Password:** If you use Gmail and have 2-Factor Authentication enabled, you **must** generate an "App password" for `EMAIL_APP_PASSWORD`. Go to your Google Account -> Security -> App passwords.

5.  **Initialize the Database:**
    The database will be initialized automatically when the FastAPI app starts, but you can also run it manually:
    ```bash
    python -c "from app.database import init_db; init_db()"
    ```

## Running the Application

To start the FastAPI server, run:

```bash
python run.py
````

The application will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

  * **API Documentation:** `http://127.0.0.1:8000/docs` (Swagger UI) or `http://127.0.0.1:8000/redoc` (ReDoc)
  * **`POST /check-mails`**:
      * **Description:** Triggers the email processing workflow. Fetches unseen emails, classifies them, and sends automated replies for "Important for Business" emails.
      * **Headers:** `X-API-Key: your_super_secret_api_key`
  * **`GET /dashboard`**:
      * **Description:** Retrieves a list of all classified emails stored in the database.
      * **Headers:** `X-API-Key: your_super_secret_api_key`

## How it Works

1.  **FastAPI:** Provides the web interface to interact with the system.
2.  **`config.py`:** Loads environment variables securely.
3.  **`schemas.py`:** Defines the data structures for API requests/responses and the LangGraph state.
4.  **`email_client.py`:** Handles the low-level IMAP (fetching) and SMTP (sending) email operations.
5.  **`database.py`:** Manages interactions with the SQLite database for persistent storage of email data.
6.  **`langgraph_agent.py`:**
      * Defines the `AgentState` which holds information about the current email being processed.
      * Contains several "nodes":
          * `fetch_and_set_email`: Gets the next email from the batch.
          * `classify_email`: Uses `langchain-groq` to call an LLM for classification. \# Changed line 2
          * `generate_response`: Prepares the response content (currently fixed).
          * `send_email_response`: Sends the email using `email_client.py` and checks for duplicates via `database.py`.
          * `store_email_data`: Saves the email and its classification to the database.
      * Defines the "edges" (transitions) between these nodes based on the email's classification and processing status, forming a directed graph.
7.  **`run.py`:** The entry point that starts the FastAPI server.

## Optional Enhancements (Future Work)

  * **Advanced Rate Limiting:** Implement more sophisticated rate limiting using a dedicated library or a token bucket algorithm.
  * **Dynamic Response Generation:** Use the LLM (**Groq**) to generate dynamic and personalized email replies based on the content of the "Important for Business" emails. \# Changed line 3
  * **Error Handling and Logging:** More robust error handling and comprehensive logging for production environments.
  * **Asynchronous Email Operations:** Use `asyncio` with `aiomail` or similar libraries for non-blocking email I/O.
  * **Frontend Dashboard:** Develop a simple web frontend to visualize the dashboard data more interactively.
  * **More Sophisticated Authentication:** Integrate with OAuth providers (e.g., Google Sign-In) for better user management.
  * **Memory for LLM:** Implement a more complex memory for the LLM (**Groq**) to remember past conversations or actions related to a sender/topic. \# Changed line 4

<!-- end list -->
