import math
import json
import pytz
from datetime import datetime, timedelta
from calendar_service import get_calendar_service
from typing import List, Dict, Any, Optional


session = dict()
session['start_time'] = datetime.utcnow()

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
            "But first, what's your name?"
        )

def get_calendar_availability(date: str, duration_minutes: int = 60, start_after_datetime: Optional[datetime] = None) -> List[Dict[str, str]]:
    try:
        utc_tz = pytz.UTC
        start_of_day_naive = datetime.strptime(f"{date} 08:00", "%Y-%m-%d %H:%M")
        end_of_day_naive = datetime.strptime(f"{date} 18:00", "%Y-%m-%d %H:%M")
        start_of_day = utc_tz.localize(start_of_day_naive)
        end_of_day = utc_tz.localize(end_of_day_naive)
        
        # Handle start_after_datetime (assume UTC if provided)
        if start_after_datetime:
            current_time = max(start_of_day, start_after_datetime)
        else:
            current_time = start_of_day
        
        print(f"DEBUG: Fetching availability for {date} from {current_time} to {end_of_day} (UTC)")  # Debug
        
        service = get_calendar_service()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Debug: Print all events for the day
        print(f"DEBUG: Found {len(events)} events on {date}:")
        for event in events:
            start_str = event['start'].get('dateTime', event['start'].get('date') + 'T00:00:00')
            end_str = event['end'].get('dateTime', event['end'].get('date') + 'T00:00:00')
            summary = event.get('summary', 'No Title')
            print(f"  - {start_str} to {end_str}: {summary}")
        
        # Build busy intervals (timezone-aware)
        busy_intervals = []
        for event in events:
            event_start_str = event['start'].get('dateTime', event['start'].get('date') + 'T00:00:00')
            event_end_str = event['end'].get('dateTime', event['end'].get('date') + 'T00:00:00')
            
            # Parse event times as UTC
            if 'Z' in event_start_str:
                event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
            else:
                event_start_naive = datetime.fromisoformat(event_start_str)
                event_start = utc_tz.localize(event_start_naive)
            
            if 'Z' in event_end_str:
                event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
            else:
                event_end_naive = datetime.fromisoformat(event_end_str)
                event_end = utc_tz.localize(event_end_naive)
            
            busy_intervals.append((event_start, event_end))
        
        available_slots = []
        slot_duration = timedelta(minutes=duration_minutes)
        slot_step = timedelta(minutes=30)
        
        while current_time + slot_duration <= end_of_day:
            slot_end = current_time + slot_duration
            
            # Check overlap
            is_available = True
            for busy_start, busy_end in busy_intervals:
                if not (slot_end <= busy_start or current_time >= busy_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start": current_time.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M")
                })
            
            current_time += slot_step
        
        print(f"DEBUG: Generated {len(available_slots)} available slots.")  # Debug
        return available_slots
        
    except Exception as e:
        print(f"Error getting availability: {e}")
        return []



def is_time_slot_available(date: str, time: str, duration_minutes: int = 60) -> bool:
    """
    Check if a specific time slot is available.
    
    Args:
        date (str): YYYY-MM-DD
        time (str): HH:MM (24-hour format)
        duration_minutes (int): Duration of the meeting in minutes
        
    Returns:
        bool: True if the time slot is available
    """
    try:
        # Create timezone-aware datetimes (UTC)
        utc_tz = pytz.UTC
        requested_start_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        requested_start = utc_tz.localize(requested_start_naive)
        requested_end = requested_start + timedelta(minutes=duration_minutes)
        
        print(f"DEBUG: Checking availability for {requested_start} to {requested_end} (UTC)")  # Debug log
        
        service = get_calendar_service()
        
        # Query events with timezone-aware ISO strings
        events_result = service.events().list(
            calendarId='primary',
            timeMin=requested_start.isoformat(),  # Already includes timezone
            timeMax=requested_end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Debug: Print any events found
        if events:
            print(f"DEBUG: Found {len(events)} overlapping events:")
            for event in events:
                start_str = event['start'].get('dateTime', event['start'].get('date'))
                end_str = event['end'].get('dateTime', event['end'].get('date'))
                summary = event.get('summary', 'No Title')
                print(f"  - {start_str} to {end_str}: {summary}")
        else:
            print("DEBUG: No overlapping events found - slot is available.")
        
        # If there are any events in this time range, the slot is not available
        return len(events) == 0
        
    except Exception as e:
        print(f"Error checking time slot availability: {e}")
        return False


# Additional helper function to get formatted availability
def get_formatted_availability(date: str, duration_minutes: int = 60) -> str:
    """
    Get formatted available time slots for display.
    """
    available_slots = get_calendar_availability(date, duration_minutes)
    
    if not available_slots:
        return f"No available time slots found for {date} with {duration_minutes} minute meetings."
    
    slots_info = "\n".join([f"• {slot['start']} - {slot['end']}" for slot in available_slots])
    return f"Available time slots for {date}:\n{slots_info}"


def schedule_google_meet(date: str, time: str, subject: str, duration_minutes: int = 60) -> str:
    if not date or not time or not subject:
        return "⚠️ Please provide the date (YYYY-MM-DD), time (HH:MM), and subject to schedule a meeting."

    # Check availability (now timezone-aware)
    if not is_time_slot_available(date, time, duration_minutes):
        # Get alternatives
        alternatives = get_calendar_availability(date, duration_minutes)
        alt_slots = [f"{slot['start']}-{slot['end']}" for slot in alternatives[:3]]  # Limit to 3
        return f"❌ The time slot {time} on {date} is not available. Here are some alternatives: {alt_slots}. Please choose one."

    try:
        utc_tz = pytz.UTC
        dt_start_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        dt_start = utc_tz.localize(dt_start_naive)
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

        entry_points = event.get("conferenceData", {}).get("entryPoints", [])
        meet_link = entry_points[0]["uri"] if entry_points else "No Meet link"

        if "meetings" not in session:
            session["meetings"] = []
        session["meetings"].append({
            "subject": subject,
            "datetime": dt_start.isoformat(),
            "link": meet_link
        })

        return f"✅ Meeting '{subject}' scheduled!\n📅 {dt_start} UTC\n🔗 Meet link: {meet_link}"

    except Exception as e:
        print(f"Error scheduling meeting: {e}")
        return "❌ Sorry, I couldn’t schedule the meeting right now. Please try again or contact support."
    

def parse_time(time_str: str) -> str:
    """
    Convert user-friendly time strings (e.g., "9:00 AM") to 24-hour format (e.g., "09:00").
    
    Args:
        time_str (str): Input time like "9:00 AM" or "14:30".
    
    Returns:
        str: Normalized "HH:MM" or original if already valid.
    
    Raises:
        ValueError: If parsing fails completely.
    """
    if not time_str:
        raise ValueError("Time string cannot be empty.")
    
    # Try 12-hour format with AM/PM
    try:
        dt = datetime.strptime(time_str, "%I:%M %p")
        return dt.strftime("%H:%M")
    except ValueError:
        pass  # Not 12-hour, try next
    
    # Try 24-hour format (e.g., "09:00" or "9:00")
    try:
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%H:%M")  # Ensures leading zero
    except ValueError:
        pass
    
    # Try without leading zero (e.g., "9:00")
    try:
        dt = datetime.strptime(time_str, "%-H:%M")  # %-H for no leading zero (Unix-like)
        return dt.strftime("%H:%M")
    except ValueError:
        pass
    
    # If all fail, return original (assume it's already valid or handle in caller)
    print(f"Warning: Could not parse time '{time_str}', using as-is.")
    return time_str
