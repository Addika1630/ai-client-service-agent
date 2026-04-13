# from dotenv import load_dotenv
# load_dotenv()
import os

session = dict()

def greet_user_and_ask_name() -> str:
    """Greet the user, ask their name if not set, and explain what the assistant can do."""
    if session.get("name"):
        return (
            f"👋 Hi {session['name']}! I can help you with:\n"
            "- Answering company FAQs\n"
            "- Creating support tickets for issues that need further assistance\n"
            "- Providing status updates on existing support tickets\n\n"
            "What would you like to do today?"
        )
    else:
        return (
            "👋 Hi there! I can help you with:\n"
            "- Answering company FAQs\n"
            "- Creating support tickets for issues that need further assistance\n"
            "- Providing status updates on existing support tickets\n\n"
            "But first, what's your name?"
        )
