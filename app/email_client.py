import imaplib
import email
import smtplib
from email.mime.text import MIMEText
import re

from app.config import settings

def fetch_unseen_emails():
    """
    Connects to the IMAP server and fetches all unseen emails from the inbox.
    Returns a list of dictionaries, each representing an email.
    """
    try:
        mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        mail.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
        mail.select('inbox')

        status, email_ids = mail.search(None, 'UNSEEN')
        email_id_list = email_ids[0].split()
        emails = []

        for num in email_id_list:
            status, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            subject = msg['subject'] if msg['subject'] else "(No Subject)"
            sender = msg['from'] if msg['from'] else "(Unknown Sender)"
            message_id = msg['Message-ID'] if msg['Message-ID'] else f"<{num.decode()}@{settings.IMAP_SERVER}>" # Fallback ID

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdisp = str(part.get('Content-Disposition'))

                    # Prefer plain text over HTML, and avoid attachments
                    if ctype == 'text/plain' and 'attachment' not in cdisp:
                        try:
                            body = part.get_payload(decode=True).decode('utf-8')
                        except UnicodeDecodeError:
                            body = part.get_payload(decode=True).decode('latin-1', errors='ignore')
                        break # Take the first plain text part
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8')
                except UnicodeDecodeError:
                    body = msg.get_payload(decode=True).decode('latin-1', errors='ignore')

            emails.append({
                "message_id": message_id,
                "subject": subject,
                "sender": sender,
                "body": body
            })
        mail.logout()
        print(f"Successfully fetched {len(emails)} unseen emails.")
        return emails
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

def send_email_reply(to_address: str, subject: str, body_content: str) -> bool:
    """
    Sends an email reply using the configured SMTP server.
    Returns True on success, False on failure.
    """
    try:
        msg = MIMEText(body_content)
        msg['Subject'] = subject
        msg['From'] = settings.EMAIL_ADDRESS
        msg['To'] = to_address

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(settings.EMAIL_ADDRESS, settings.EMAIL_APP_PASSWORD)
            server.send_message(msg)
        print(f"Reply sent to {to_address} with subject: '{subject}'")
        return True
    except Exception as e:
        print(f"Error sending email reply to {to_address}: {e}")
        return False

if __name__ == "__main__":
    # Example usage for testing the email client
    print("--- Testing Email Client ---")
    print("Fetching unseen emails...")
    emails = fetch_unseen_emails()
    if emails:
        for i, mail in enumerate(emails):
            print(f"\n--- Email {i+1} ---")
            print(f"Message-ID: {mail['message_id']}")
            print(f"Subject: {mail['subject']}")
            print(f"From: {mail['sender']}")
            print(f"Body (first 200 chars): {mail['body'][:200]}...")
            if len(mail['body']) > 200:
                print("...")
        # Example of sending a reply (uncomment to test, use a valid recipient)
        # test_recipient = "your_other_email@example.com"
        # print(f"\nAttempting to send a test reply to {test_recipient}...")
        # success = send_email_reply(test_recipient, "Test Reply from SmartMail AI", "This is a test reply from the SmartMail AI agent. Please ignore.")
        # if success:
        #     print("Test reply sent successfully.")
        # else:
        #     print("Failed to send test reply.")
    else:
        print("No unseen emails found or error occurred.")
    print("--- Email Client Test Complete ---")