from fastapi import Request
from typing import Iterable
from app.constants.constants import *
from app.errors.base_exception import AppException
from typing import Callable, Any, Dict


def require_roles(*allowed_roles: Iterable[str]) -> Callable[[Request], Dict[str, Any]]:
    def role_dependency(request: Request) -> Dict[str, Any]:
        claims = getattr(request.state, "user", None)

        if not claims:
            raise AppException(AUTH_003)

        user_role = claims.get("role")

        if user_role not in allowed_roles:
            raise AppException(AUTH_004)

        return claims

    return role_dependency
