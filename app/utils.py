# This file is for general utility functions that don't fit into other modules.
# Currently, it's empty, but it's good practice to have it for future expansion.

# Example of a potential utility function:
def format_email_address(full_address: str) -> str:
    """Extracts just the email address from a 'Name <email@example.com>' string."""
    import re
    match = re.search(r'<([^>]+)>', full_address)
    return match.group(1) if match else full_address