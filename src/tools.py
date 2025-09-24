# from dotenv import load_dotenv
# load_dotenv()
import math
from datetime import datetime, timedelta
from calendar_service import get_calendar_service
from datetime import datetime, timedelta, timezone
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




# session is expected to be a module-level dict (already present in your code)
# session = dict()

def schedule_google_meet(date: str, time: str, subject: str, duration_minutes: int = 60) -> str:
    """
    Schedule a Google Meet meeting via Google Calendar.
    - Prevents double-booking (checks both local session and Google Calendar).
    - Avoids scheduling during midnight hours (00:00–06:00 UTC).
    - Returns a user-friendly status string.
    """

     # Acquire calendar service (may raise if auth expired)
    try:
        service = get_calendar_service()
    except Exception as e:
        # Surface auth-level problems early and clearly
        err = str(e)
        if "invalid_grant" in err or "expired" in err or "revoked" in err:
            return (
                "❌ Calendar authentication error: credentials expired or revoked. "
                "Please re-authenticate (regenerate token.json / refresh tokens)."
            )
        return f"❌ Error obtaining calendar service: {e}"

    if not date or not time or not subject:
        return "⚠️ Please provide the date (YYYY-MM-DD), time (HH:MM), and subject to schedule a meeting."

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
            available = get_next_available_slots(service)
            return (
                "⚠️ Please use a valid date and time. Meetings cannot be scheduled in the past.\n\n"
                "Here are some available slots you can pick:\n" +
                "\n".join(f"- {slot}" for slot in available)
            )
        # Disallow midnight hours (00:00 - 06:00 UTC)
        if dt_start.hour < 6:
            available = get_next_available_slots(service)
            return (
                "⚠️ Meetings cannot be scheduled between 00:00 and 06:00 UTC.\n\n"
                "Here are some available slots:\n" +
                "\n".join(f"- {slot}" for slot in available)
            )
            
        # Check local in-memory session for overlap (use proper interval overlap check)
        for m in session.get("meetings", []):
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
                available = get_next_available_slots(service)
                return (
                    f"⚠️ That time slot is already booked ({existing_start.strftime('%Y-%m-%d %H:%M')} - "
                    f"{existing_end.strftime('%H:%M')} UTC).\n\n"
                    "Here are some available slots:\n" +
                    "\n".join(f"- {slot}" for slot in available)
                )


        # Query Google Calendar for potential conflicts.
        # Use a small search margin to catch events that start earlier but end during requested slot.
        search_margin = timedelta(hours=1)
        time_min = (dt_start - search_margin).isoformat()
        time_max = (dt_end + search_margin).isoformat()

        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        items = events_result.get("items", [])
        for ev in items:
            # start and end may be 'dateTime' (timed) or 'date' (all-day)
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
                available = get_next_available_slots(service)
                return (
                    f"⚠️ That time slot is already booked ({existing_start.strftime('%Y-%m-%d %H:%M')} - "
                    f"{existing_end.strftime('%H:%M')} UTC).\n\n"
                    "Here are some available slots:\n" +
                    "\n".join(f"- {slot}" for slot in available)
                )

        # No conflicts -> create the event with conferenceData to get a Meet link
        event_body = {
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
            body=event_body,
            conferenceDataVersion=1
        ).execute()

        # Safely extract Meet link
        entry_points = event.get("conferenceData", {}).get("entryPoints", [])
        meet_link = entry_points[0]["uri"] if entry_points else "No Meet link"

        # Persist meeting in session with duration for future checks
        session.setdefault("meetings", []).append({
            "subject": subject,
            "datetime": dt_start.isoformat(),
            "link": meet_link,
            "duration_minutes": duration_minutes
        })

        return f"✅ Meeting '{subject}' scheduled!\n📅 {dt_start.strftime('%Y-%m-%d %H:%M')} UTC\n🔗 Meet link: {meet_link}"

    except Exception as e:
        err_str = str(e)
        # If auth problem surfaces here (from Google API library), provide a helpful hint
        if "invalid_grant" in err_str or "expired" in err_str or "revoked" in err_str:
            return (
                "❌ Authentication error while scheduling: calendar credentials expired or revoked. "
                "Please re-authenticate."
            )
        return f"❌ Error scheduling meeting: {e}"

def get_next_available_slots(service, days_ahead: int = 4, slots_per_day: int = 4):
    """Return a list of available slots over the next few days."""
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
            events_result = service.events().list(
                calendarId="primary",
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


