from fastapi import HTTPException
from app.errors.error_registry import ERROR_REGISTRY, ErrorDefinition
from app.constants.constants import *


class AppException(HTTPException):
    def __init__(self, error_code: str, message: str | None = None):
        error_def: ErrorDefinition = ERROR_REGISTRY.get(error_code)

        if not error_def:
            error_code: str = SYS_001
            error_def: ErrorDefinition = ERROR_REGISTRY.get(error_code)

        
        super().__init__(
            status_code=error_def.http_status,
            detail=message or error_def.message
        )

        self.error_code = error_code