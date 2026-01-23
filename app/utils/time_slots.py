from datetime import datetime, time, timedelta, timezone

def get_available_slots(date_str, local_tz_offset_hours=5.5):
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    now_utc = datetime.now(timezone.utc)
    
    shifts = [(time(9, 0), time(12, 0)), (time(13, 0), time(17, 0))]
    duration = timedelta(minutes=20)
    local_tz = timezone(timedelta(hours=local_tz_offset_hours))
    available_slots = []

    for start_t, end_t in shifts:
        current_time = datetime.combine(target_date, start_t, tzinfo=local_tz)
        shift_end = datetime.combine(target_date, end_t, tzinfo=local_tz)

        while current_time + duration <= shift_end:
            utc_start = current_time.astimezone(timezone.utc)
            
            if utc_start > now_utc:
                available_slots.append({
                    "start": utc_start.isoformat(),
                    "end": (utc_start + duration).isoformat()
                })
            current_time += duration
            
    return available_slots
