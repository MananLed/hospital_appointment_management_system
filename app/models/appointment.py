from enum import Enum
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timezone
from uuid import UUID, uuid4 

class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(BaseModel):
    id: str = Field(alias="id", default_factory=lambda: str(uuid4()))
    timeslot: str = Field(alias="timeslot")
    email: EmailStr = Field(alias="email")
    status: AppointmentStatus = Field(alias="status")
    department: str = Field(alias="department")
    doctor_name: str = Field(alias="doctor_name")
    created_at: datetime = Field(alias="created_at", default_factory=lambda: datetime.now(timezone.utc))