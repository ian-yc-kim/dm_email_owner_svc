def build_email_owner_prompt(html_content: str, emails: list[str]) -> list[dict]:
    """Constructs prompt messages for mapping emails to owners from given HTML content.

    The system prompt instructs the assistant to extract display names corresponding to the provided email addresses from the HTML content.
    The user prompt embeds the provided HTML content and a comma-separated list of email addresses.

    Returns:
        A list containing two dictionaries, one for the 'system' role and one for the 'user' role.
    """
    # Define the system prompt with the assistant's role
    system_prompt = (
        "You are an assistant that extracts display names from HTML content for given email addresses. "
        "For each email, identify the corresponding owner's display name from the provided HTML content. "
        "If an email is not found or no corresponding display name exists, return null for that owner. "
        "Return only a JSON array of objects with keys 'email' and 'owner', with no additional text."
    )

    # Create a comma-separated string of email addresses
    email_list_str = ", ".join(emails)

    # Define the user prompt which includes the HTML content and the emails
    user_prompt = (
        f"Extract the owner's display name for each of the following emails from the HTML content provided below.\n\n"
        f"HTML Content:\n{html_content}\n\n"
        f"Emails: {email_list_str}\n\n"
        f"Respond with a JSON array of objects with keys 'email' and 'owner' only."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
