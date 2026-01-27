from enum import Enum
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from datetime import datetime, timezone, date
from uuid import uuid4


class AppointmentStatus(str, Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(BaseModel):

    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    id: str = Field(alias="id", default_factory=lambda: str(uuid4()))
    timeslot: str = Field(alias="timeslot")
    email: EmailStr = Field(alias="email")
    status: AppointmentStatus = Field(alias="status", default=AppointmentStatus.BOOKED)
    department: str = Field(alias="department")
    doctor_name: str = Field(alias="doctor_name")
    doctor_id: str = Field(alias="doctor_id")
    patient_id: str = Field(alias="patient_id")
    appointment_date: date = Field(alias="date")
    created_at: datetime = Field(
        alias="created_at", default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("appointment_date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        elif isinstance(v, date):
            return v
        else:
            raise ValueError("Invalid date format")
