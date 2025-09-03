# from dotenv import load_dotenv
# load_dotenv()
import math
from datetime import datetime, timedelta
from calendar_service import get_calendar_service
session = dict()

def greet_user_and_ask_name() -> str:
    """Greet the user, ask their name if not set, and explain what the assistant can do."""
    if session.get("name"):
        return (
            f"👋 Hi {session['name']}! I can help you with:\n"
            "- Answering company FAQs\n"
            "- Connecting you to a live support agent\n"
            "- Scheduling a meeting to learn more about our services/products\n\n"
            "What would you like to do today?"
        )
    else:
        return (
            "👋 Hi there! I can help you with:\n"
            "- Answering company FAQs\n"
            "- Connecting you to a live support agent\n"
            "- Scheduling a meeting to learn more about our services/products\n\n"
            "But first, what’s your name?"
        )


def schedule_google_meet(date: str, time: str, subject: str, duration_minutes: int = 60) -> str:
    """
    Schedule a Google Meet meeting via Google Calendar.
    User must provide date, time, and subject.
    """
    if not date or not time or not subject:
        return "⚠️ Please provide the date (YYYY-MM-DD), time (HH:MM), and subject to schedule a meeting."

    try:
        service = get_calendar_service()

        # Start & end times
        dt_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        dt_end = dt_start + timedelta(minutes=duration_minutes)

        event = {
            "summary": subject,
            "start": {"dateTime": dt_start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": dt_end.isoformat(), "timeZone": "UTC"},
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{int(datetime.now().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        }

        event = service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1
        ).execute()

        # Extract Meet link safely
        entry_points = event.get("conferenceData", {}).get("entryPoints", [])
        meet_link = entry_points[0]["uri"] if entry_points else "No Meet link"

        # Save to session memory
        if "meetings" not in session:
            session["meetings"] = []
        session["meetings"].append({
            "subject": subject,
            "datetime": dt_start.isoformat(),
            "link": meet_link
        })

        return f"✅ Meeting '{subject}' scheduled!\n📅 {dt_start} UTC\n🔗 Meet link: {meet_link}"

    except Exception as e:
        return "❌ Sorry, I couldn’t schedule the meeting right now. Please try again or contact support."
