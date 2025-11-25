# from dotenv import load_dotenv
# load_dotenv()
import os
import math
from datetime import datetime, timedelta
from calendar_service import get_calendar_service
from datetime import datetime, timedelta, timezone
from calendar_service import get_calendar_service
from calendar_service import get_calendar_service_for_team
import smtplib
import os
import uuid
from email.mime.text import MIMEText
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




# session is expected to be a module-level dict (already present in your code)
# session = dict()

def schedule_google_meet(date: str, time: str, subject: str, email: str, duration_minutes: int = 60, team: str = None) -> str:
    """
    Schedule a Google Meet meeting via Google Calendar.
    - Prevents double-booking (checks both local session and Google Calendar).
    - Avoids scheduling during midnight hours (00:00–06:00 UTC).
    - Requires client email and sends an invite.
    - Requires an explicit team selection ("technical" or "sales").
    - Returns a user-friendly status string.
    """

    # Require explicit, valid team selection; do NOT silently default
    team = (team or "").strip().lower()
    if team not in {"technical", "sales"}:
        return (
            "⚠️ To schedule a meeting, please specify which team you would like to meet: "
            "Sales or Technical."
        )

    calendar_id = os.getenv(f"CAL_{team.upper()}_CALENDAR_ID", "primary")
    team_title = team.capitalize()

    # Acquire calendar service for team (may raise if auth expired)
    try:
        service = get_calendar_service_for_team(team)
    except Exception as e:
        # Surface auth-level problems early and clearly
        err = str(e)
        if "invalid_grant" in err or "expired" in err or "revoked" in err:
            return (
                "❌ Calendar authentication error: credentials expired or revoked. "
                "Please re-authenticate (regenerate token.json / refresh tokens)."
            )
        return f"❌ Error obtaining calendar service: {e}"

    # Require all fields including email
    if not date or not time or not subject or not email:
        return "⚠️ Please provide the date (YYYY-MM-DD), time (HH:MM UTC), subject, and your email address to schedule a meeting."

    # Helper to parse RFC3339 / Google dateTime strings robustly
    def _parse_rfc3339(dt_str):
        if not dt_str:
            return None
        # Google may return '2025-09-17T10:00:00Z' — replace Z with +00:00 to be safe
        if dt_str.endswith("Z"):
            dt_str = dt_str[:-1] + "+00:00"
        return datetime.fromisoformat(dt_str)

    try:
        # Build timezone-aware start/end in UTC
        dt_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        dt_end = dt_start + timedelta(minutes=duration_minutes)

        # ⛔ Disallow scheduling in the past
        if dt_start < datetime.now(timezone.utc):
            available = get_next_available_slots(service, calendar_id)
            return (
                "⚠️ Please use a valid date and time. Meetings cannot be scheduled in the past.\n\n"
                "Here are some available slots you can pick:\n" +
                "\n".join(f"- {slot}" for slot in available)
            )

        # Disallow midnight hours (00:00 - 06:00 UTC)
        if dt_start.hour < 6:
            available = get_next_available_slots(service, calendar_id)
            return (
                "⚠️ Meetings cannot be scheduled between 00:00 and 06:00 UTC.\n\n"
                "Here are some available slots:\n" +
                "\n".join(f"- {slot}" for slot in available)
            )
            
        # Check local in-memory session for overlap (use proper interval overlap check)
        for m in session.get("meetings", []):
            if m.get("team") != team:
                continue
            try:
                existing_start = datetime.fromisoformat(m["datetime"])
                if existing_start.tzinfo is None:
                    existing_start = existing_start.replace(tzinfo=timezone.utc)
            except Exception:
                # If stored datetime can't be parsed, skip it
                continue
            existing_duration = m.get("duration_minutes", duration_minutes)
            existing_end = existing_start + timedelta(minutes=existing_duration)
            # overlap check: new_start < existing_end and new_end > existing_start
            if dt_start < existing_end and dt_end > existing_start:
                available = get_next_available_slots(service, calendar_id)
                return (
                    f"Unfortunately, the requested time slot ({dt_start.strftime('%Y-%m-%d %H:%M')} UTC) is already booked. "
                    f"However, I can offer you a list of available meeting slots for the {team_title} team:\n"
                    + "\n".join(available) +
                    "\nPlease choose an available time slot, and I will be happy to schedule a meeting for you."
                )

        # Query Google Calendar for potential conflicts.
        search_margin = timedelta(hours=1)
        time_min = (dt_start - search_margin).isoformat()
        time_max = (dt_end + search_margin).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        items = events_result.get("items", [])
        for ev in items:
            start_field = ev.get("start", {})
            end_field = ev.get("end", {})

            if "dateTime" in start_field:
                existing_start = _parse_rfc3339(start_field.get("dateTime"))
                existing_end = _parse_rfc3339(end_field.get("dateTime"))
            else:
                # all-day event -> treat as whole-day block
                existing_start = datetime.fromisoformat(start_field.get("date")).replace(tzinfo=timezone.utc)
                existing_end = existing_start + timedelta(days=1)

            if existing_start is None or existing_end is None:
                continue

            # overlap check
            if dt_start < existing_end and dt_end > existing_start:
                available = get_next_available_slots(service, calendar_id)
                return (
                    f"Unfortunately, the requested time slot ({dt_start.strftime('%Y-%m-%d %H:%M')} UTC) is already booked. "
                    f"However, I can offer you a list of available meeting slots for the {team_title} team:\n"
                    + "\n".join(available) +
                    "\nPlease choose an available time slot, and I will be happy to schedule a meeting for you."
                )

        # ✅ No conflicts -> create the event with conferenceData and attendee email
        event_body = {
            "summary": subject,
            "start": {"dateTime": dt_start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": dt_end.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": email}],  # send invite to client
            "conferenceData": {
                "createRequest": {
                    "requestId": f"meet-{int(datetime.now().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }
        }

        event = service.events().insert(
            calendarId=calendar_id,
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all"  # ensures email invite is sent
        ).execute()

        # Safely extract Meet link
        entry_points = event.get("conferenceData", {}).get("entryPoints", [])
        meet_link = entry_points[0]["uri"] if entry_points else "No Meet link"

        # Persist meeting in session with duration for future checks
        session.setdefault("meetings", []).append({
            "subject": subject,
            "datetime": dt_start.isoformat(),
            "link": meet_link,
            "duration_minutes": duration_minutes,
            "email": email,
            "team": team
        })

        return f"✅ Meeting '{subject}' scheduled!\n📅 {dt_start.strftime('%Y-%m-%d %H:%M')} UTC\n📧 Invite sent to {email}\n🔗 Meet link: {meet_link}"

    except Exception as e:
        err_str = str(e)
        if "invalid_grant" in err_str or "expired" in err_str or "revoked" in err_str:
            return (
                "❌ Authentication error while scheduling: calendar credentials expired or revoked. "
                "Please re-authenticate."
            )
        return f"❌ Error scheduling meeting: {e}"


def get_next_available_slots(service, calendar_id: str, days_ahead: int = 4, slots_per_day: int = 4):
    """Return a list of available slots over the next few days for the given calendar_id."""
    now = datetime.now(timezone.utc)
    suggestions = []
    preferred_hours = [9, 11, 14, 16]  # change to whatever you want

    for day_offset in range(1, days_ahead + 1):
        day = (now + timedelta(days=day_offset)).date()
        for hour in preferred_hours[:slots_per_day]:
            dt_start = datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc)
            dt_end = dt_start + timedelta(minutes=60)

            # Skip if in the past or midnight range
            if dt_start < now or dt_start.hour < 6:
                continue

            # Check conflicts in Google Calendar
            search_margin = timedelta(minutes=1)
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=(dt_start - search_margin).isoformat(),
                timeMax=(dt_end + search_margin).isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            items = events_result.get("items", [])
            if any(True for ev in items):
                continue

            # If no conflicts -> add suggestion
            suggestions.append(dt_start.strftime("%Y-%m-%d %H:%M UTC"))

    return suggestions[:days_ahead * slots_per_day]


def available_slots(days_ahead: int = 4, slots_per_day: int = 4, team: str = None):
    """Return a list of available slots over the next few days."""
    # Acquire calendar service (may raise if auth expired)
    try:
        team = (team or "").strip().lower()
        if team not in {"technical", "sales"}:
            return (
                "⚠️ To show available meeting slots, please specify which team you would like to meet: "
                "Sales or Technical."
            )
        service = get_calendar_service_for_team(team)
    except Exception as e:
        # Surface auth-level problems early and clearly
        err = str(e)
        if "invalid_grant" in err or "expired" in err or "revoked" in err:
            return (
                "❌ Calendar authentication error: credentials expired or revoked. "
                "Please re-authenticate (regenerate token.json / refresh tokens)."
            )
        return f"❌ Error obtaining calendar service: {e}"

    now = datetime.now(timezone.utc)
    suggestions = []
    preferred_hours = [9, 11, 14, 16]  # change to whatever you want

    for day_offset in range(0, days_ahead):
        day = (now + timedelta(days=day_offset)).date()
        for hour in preferred_hours[:slots_per_day]:
            dt_start = datetime(day.year, day.month, day.day, hour, 0, tzinfo=timezone.utc)
            dt_end = dt_start + timedelta(minutes=60)

            # Skip if in the past or midnight range
            if dt_start < now or dt_start.hour < 6:
                continue

            # Check conflicts against session
            conflict = False
            for m in session.get("meetings", []):
                existing_start = datetime.fromisoformat(m["datetime"])
                if existing_start.tzinfo is None:
                    existing_start = existing_start.replace(tzinfo=timezone.utc)
                existing_end = existing_start + timedelta(minutes=m.get("duration_minutes", 60))
                if dt_start < existing_end and dt_end > existing_start:
                    conflict = True
                    break

            if conflict:
                continue

            # Check conflicts in Google Calendar
            search_margin = timedelta(minutes=1)
            calendar_id = os.getenv(f"CAL_{team.upper()}_CALENDAR_ID", "primary")
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=(dt_start - search_margin).isoformat(),
                timeMax=(dt_end + search_margin).isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            items = events_result.get("items", [])
            if any(True for ev in items):
                continue

            # If no conflicts -> add suggestion
            suggestions.append(dt_start.strftime("%Y-%m-%d %H:%M UTC"))

    return suggestions[:days_ahead * slots_per_day]

# Global variable to track support request state
support_request_state = {}


def smart_support_router(user_message: str, client_email: str = None, client_name: str = None) -> str:
    """
    Simple support router that sends email when all information is provided.
    """
    
    # Extract email from message if not provided
    if not client_email:
        client_email = extract_email_from_text(user_message)

    cleaned_message = user_message.strip()

    # If we have email and a substantial message, send email immediately
    if client_email and len(cleaned_message) > 40:
        return send_support_email_direct(
            user_message=cleaned_message,
            client_email=client_email,
            client_name=client_name
        )
    
    # If we have email but short message, ask for a brief but clear description
    if client_email:
        return (
            "Thank you. Before I connect you to our human support team, "
            "please briefly describe the issue (1–3 sentences) so they understand your request."
        )
    
    # If no email detected, ask for email
    return (
        "I'd be happy to connect you with our support team. "
        "Please provide the email address where they can contact you."
    )

def extract_email_from_text(text: str) -> str:
    """Extract email address from text"""
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def send_support_email_direct(user_message: str, client_email: str, client_name: str = None) -> str:
    """
    Direct function to send email to support team.
    """
    
    SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "addisu05mulat@gmail.com")
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "addisu05mulat@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return (
            "❌ Email configuration error: SMTP credentials are not set correctly. "
            "Please contact the system administrator."
        )

    timestamp = datetime.now().strftime("%Y-%m-%d")
    unique_id = uuid.uuid4().hex[:6].upper()
    subject = f"Support Request #{unique_id} - {timestamp}"
    client_display_name = client_name or client_email

    body = f"""New Client Support Request

Client: {client_display_name}
Email: {client_email}
Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Request ID: {unique_id}

Client's Message:
{user_message}

---
Please reply directly to {client_email}.
"""

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["To"] = SUPPORT_EMAIL
        msg["From"] = SMTP_USERNAME
        msg["Reply-To"] = client_email

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, [SUPPORT_EMAIL], msg.as_string())

        return (
            "✅ I've sent your request to our support team.\n\n"
            "**What happens next:**\n"
            f"- Our support team will contact you directly at **{client_email}**\n"
            f"- **Reference ID:** {unique_id}\n\n"
            "Thank you for reaching out! Our team will be in touch soon."
        )

    except Exception as e:
        return f"❌ Sorry, I encountered an error while sending your request: {e}"


