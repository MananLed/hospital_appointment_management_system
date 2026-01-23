from datetime import datetime, date
from pydantic import BaseModel, field_validator

class DateQuery(BaseModel):
    appointment_date: str 

    @field_validator("appointment_date")
    @classmethod
    def validate_strict_date_format(cls, appointment_date: str) -> str:
        try:
            datetime.strptime(appointment_date, "%Y-%m-%d").date()
            return appointment_date
        except ValueError as e:
            print(e)
            raise ValueError("Date must be in YYYY-MM-DD format and a valid calendar day")