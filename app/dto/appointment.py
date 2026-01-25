from datetime import datetime, date
from pydantic import BaseModel, field_validator, Field, ConfigDict
from app.models.user import Department
from typing import TypedDict

class DateQuery(BaseModel):

    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    appointment_date: date = Field(alias="appointment_date")

    @field_validator("appointment_date", mode="before")
    @classmethod
    def validate_and_parse_date(cls, v):
        if isinstance(v, str):
            try:
                parsed_date = datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format and a valid calendar day")
        elif isinstance(v, date):
            parsed_date = v
        else:
            raise ValueError("Invalid date value")

        if parsed_date < date.today():
            raise ValueError("Appointment date cannot be in the past")

        return parsed_date
    
class DateQueryDoctor(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    appointment_date: date = Field(alias="appointment_date")

    @field_validator("appointment_date", mode="before")
    @classmethod
    def validate_and_parse_date(cls, v):
        if isinstance(v, str):
            try:
                parsed_date = datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format and a valid calendar day")
        elif isinstance(v, date):
            parsed_date = v
        else:
            raise ValueError("Invalid date value")

        return parsed_date


class TimeSlot(TypedDict):

    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    start: str = Field(alias="start") 
    end: str   = Field(alias="end") 

class BookAppointmentRequest(BaseModel):

    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    department: Department = Field(alias="department")
    timeslot_start: str = Field(alias="timeslot_start")


class CancelAppointmentRequest(BaseModel):

    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    timeslot_start: str = Field(alias="timeslot_start")

class CompleteAppointmentRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    timeslot_start: str = Field(alias="timeslot_start")
    appointment_date: date = Field(alias="appointment_date")

    @field_validator("appointment_date", mode="before")
    @classmethod
    def validate_and_parse_date(cls, v):
        if isinstance(v, str):
            try:
                parsed_date = datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format and a valid calendar day")
        elif isinstance(v, date):
            parsed_date = v
        else:
            raise ValueError("Invalid date value")
        
        return parsed_date