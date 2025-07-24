import sqlite3
import datetime
from typing import Optional, Tuple

DATABASE_FILE = "emails.db"

def init_db():
    """Initializes the SQLite database and creates the 'emails' table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            subject TEXT,
            sender TEXT,
            body TEXT,
            classification TEXT,
            response_sent BOOLEAN DEFAULT FALSE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_FILE}' initialized.")

def store_email_data(message_id: str, subject: str, sender: str, body: str, classification: str, response_sent: bool = False):
    """
    Stores or updates email data in the database.
    If message_id already exists, it updates the response_sent status.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO emails (message_id, subject, sender, body, classification, response_sent)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, subject, sender, body, classification, response_sent)
        )
        conn.commit()
        print(f"Successfully stored new email: '{subject}' (ID: {message_id})")
    except sqlite3.IntegrityError:
        # If message_id already exists, update the response_sent status
        print(f"Email with message_id '{message_id}' already exists. Updating response_sent status.")
        cursor.execute(
            """
            UPDATE emails SET classification = ?, response_sent = ?, timestamp = ? WHERE message_id = ?
            """,
            (classification, response_sent, datetime.datetime.now(), message_id)
        )
        conn.commit()
    except Exception as e:
        print(f"Error storing/updating email data for '{message_id}': {e}")
    finally:
        conn.close()

def get_email_by_message_id(message_id: str) -> Optional[Tuple]: #-> tuple | None:
    """
    Retrieves an email record from the database by its message_id.
    Returns a tuple representing the row, or None if not found.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails WHERE message_id = ?", (message_id,))
    email_data = cursor.fetchone()
    conn.close()
    return email_data

def get_all_emails() -> list[tuple]:
    """
    Retrieves all email records from the database, ordered by timestamp (descending).
    Returns a list of tuples, each representing an email row.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emails ORDER BY timestamp DESC")
    emails = cursor.fetchall()
    conn.close()
    return emails

if __name__ == "__main__":
    # Example usage for testing the database module
    print("--- Testing Database Module ---")
    init_db()

    # Add some dummy data
    print("Adding dummy email 1...")
    store_email_data("msgid-123", "Test Subject 1", "test1@example.com", "This is a test body.", "Unwanted", False)
    print("Adding dummy email 2 (Important)...")
    store_email_data("msgid-456", "Important Meeting Request", "business@company.com", "Please confirm our appointment.", "Important", True)
    print("Adding dummy email 3...")
    store_email_data("msgid-789", "Buy cheap V1agra", "spam@bad.com", "Click here for pills!", "SPAM", False)
    print("Updating dummy email 1 (response_sent to True)...")
    store_email_data("msgid-123", "Test Subject 1", "test1@example.com", "This is a test body.", "Unwanted", True) # Simulate update

    print("\n--- All Emails in DB ---")
    all_emails = get_all_emails()
    for email_entry in all_emails:
        print(email_entry)

    print("\n--- Retrieving email by message_id 'msgid-456' ---")
    retrieved_email = get_email_by_message_id("msgid-456")
    print(retrieved_email)

    print("--- Database Module Test Complete ---")