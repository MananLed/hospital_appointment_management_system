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
    SYS_001: sys_exception
}