from app.constants.constants import *
from dataclasses import dataclass 
from fastapi import status
from typing import Dict

@dataclass(frozen=True)
class ErrorDefinition:
    http_status: int
    message: str 

db_exception: ErrorDefinition = ErrorDefinition(
    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message=DB_ERROR
)

sys_exception: ErrorDefinition = ErrorDefinition(
    http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    message=SERVER_ERROR
)

unauthorized_exception: ErrorDefinition = ErrorDefinition(
    http_status=status.HTTP_401_UNAUTHORIZED,
    message=UNAUTHORIZED_ACCESS
)


ERROR_REGISTRY: Dict[str, ErrorDefinition] = {
    HOSPITAL_001: ErrorDefinition(
        http_status=status.HTTP_400_BAD_REQUEST,
        message="Missing department value"
    ),
    AUTH_001: ErrorDefinition(
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Authorization header missing or invalid"
    ),
    AUTH_002: ErrorDefinition(
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Invalid or expired token"
    ),
    AUTH_003: ErrorDefinition(
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Authentication context missing"
    ),
    AUTH_004: unauthorized_exception,
    USER_001: ErrorDefinition(
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Invalid Credentials"
    ),
    USER_002: ErrorDefinition(
        http_status=status.HTTP_409_CONFLICT,
        message="User with given email already exists"
    ),
    USER_003: sys_exception,
    USER_004: sys_exception,
    USER_005: ErrorDefinition(
        http_status=status.HTTP_401_UNAUTHORIZED,
        message="Invalid Credentials"
    ),
    USER_006: sys_exception,
    USER_007: db_exception,
    APPOINTMENT_001: db_exception,
    APPOINTMENT_002: db_exception,
    APPOINTMENT_003: ErrorDefinition(
        http_status=status.HTTP_404_NOT_FOUND,
        message="Doctor with the given id does not exist"
    ),
    APPOINTMENT_004: ErrorDefinition(
        http_status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        message="Cannot book a past time slot"
    ),
    APPOINTMENT_005: ErrorDefinition(
        http_status=status.HTTP_409_CONFLICT,
        message="Timeslot is not valid"
    ),
    APPOINTMENT_006: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Cannot book more than 3 appointments per day"
    ),
    APPOINTMENT_007: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Multiple appointments in the same department are not allowed on the same day"
    ),
    APPOINTMENT_008: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Appointments can only be booked up to 7 days in advance"
    ),
    APPOINTMENT_009: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Available time slots can be viewed for up to 7 days in advance"
    ),
    APPOINTMENT_010: db_exception,
    APPOINTMENT_011: ErrorDefinition(
        http_status=status.HTTP_409_CONFLICT,
        message="Slot is already booked"
    ),
    APPOINTMENT_012: db_exception,
    APPOINTMENT_013: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Already have a booked request with the same time"
    ),
    APPOINTMENT_014: db_exception,
    APPOINTMENT_015: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Cannot cancel a appointment of past date"
    ),
    APPOINTMENT_016: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Appointments cannot be cancelled less than 1 hour before start time"
    ),
    APPOINTMENT_017: ErrorDefinition(
        http_status=status.HTTP_404_NOT_FOUND,
        message="Appointment with the specified details does not exist"
    ),
    APPOINTMENT_018: ErrorDefinition(
        http_status=status.HTTP_409_CONFLICT,
        message="Completed appointments cannot be cancelled"
    ),
    APPOINTMENT_019: unauthorized_exception,
    APPOINTMENT_020: db_exception,
    APPOINTMENT_021: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Future appointments cannot be marked completed"
    ),
    APPOINTMENT_022: ErrorDefinition(
        http_status=status.HTTP_404_NOT_FOUND,
        message="Appointment with the specified details does not exist"
    ),
    APPOINTMENT_023: db_exception,
    APPOINTMENT_024: ErrorDefinition(
        http_status=status.HTTP_403_FORBIDDEN,
        message="Completed request cannot be marked completed again"
    ),
    SYS_001: sys_exception
}