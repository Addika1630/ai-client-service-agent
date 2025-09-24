from datetime import datetime, timedelta
from calendar_service import get_calendar_service
from datetime import datetime, timedelta, timezone

date = "2025-09-17"
time = "22:30"
duration_minutes = 90

dt_start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
dt_end = dt_start + timedelta(minutes=duration_minutes)

print("Start:", dt_start)
print("End:", dt_end)

