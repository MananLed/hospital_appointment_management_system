from datetime import datetime, time, timedelta, timezone, date
from app.dto.appointment import TimeSlot
from typing import List
from app.constants.constants import *

def get_available_slots(appointment_date: date, local_tz_offset_hours=5.5) -> List[TimeSlot]:
    now_utc = datetime.now(timezone.utc)

    shifts = [
        (time(FIRST_SHIFT_START_TIME, 0), time(FIRST_SHIFT_END_TIME, 0)),
        (time(SECOND_SHIFT_START_TIME, 0), time(SECOND_SHIFT_END_TIME, 0))
    ]

    duration = timedelta(minutes=TIME_SLOT_INTERVAL)
    local_tz = timezone(timedelta(hours=local_tz_offset_hours))
    available_slots = []

    for start_t, end_t in shifts:
        current_time = datetime.combine(appointment_date, start_t, tzinfo=local_tz)
        shift_end = datetime.combine(appointment_date, end_t, tzinfo=local_tz)

        while current_time + duration <= shift_end:
            utc_start = current_time.astimezone(timezone.utc)

            if utc_start > now_utc:
                available_slots.append({
                    "start": utc_start.isoformat(),
                    "end": (utc_start + duration).isoformat()
                })

            current_time += duration

    return available_slots

def filter_available_slots(all_slots: List[TimeSlot], occupied_timeslots: List[str]) -> List[TimeSlot]:
    occupied_set = {
        datetime.fromisoformat(ts).astimezone(timezone.utc)
        for ts in occupied_timeslots
    }

    filtered = []

    for slot in all_slots:
        slot_start = datetime.fromisoformat(slot["start"]).astimezone(timezone.utc)

        if slot_start not in occupied_set:
            filtered.append(slot)

    return filtered

def calculate_expires_at() -> int:
    return int(
        (datetime.now(timezone.utc) + timedelta(days=TTL_DAYS)).timestamp()
    )