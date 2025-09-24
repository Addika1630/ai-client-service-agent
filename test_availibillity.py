from datetime import datetime, timedelta
import pytz  # Ensure installed: pip install pytz
# Import your functions (adjust paths as needed)
from src.tools import get_calendar_service, get_calendar_availability  # Replace with actual import

def test_availability(date: str = "2025-09-24"):
    print(f"=== Testing Availability for {date} ===")
    
    # Call the function
    slots = get_calendar_availability(date, duration_minutes=60)
    
    print(f"Returned slots: {slots}")
    if not slots:
        print("❌ No slots returned – check logs below for why.")
    else:
        print("✅ Slots found:", slots)
    
    # Force a full-day check even if empty
    start_of_day = datetime.strptime(f"{date} 08:00", "%Y-%m-%d %H:%M")
    end_of_day = datetime.strptime(f"{date} 18:00", "%Y-%m-%d %H:%M")
    print(f"Expected window: {start_of_day} to {end_of_day}")
    print(f"Slot step: 30 min, Duration: 60 min")
    print(f"Possible slots count: ~20 (if fully free)")

if __name__ == "__main__":
    test_availability()
