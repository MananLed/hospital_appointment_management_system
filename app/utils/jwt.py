from fastapi import Request
from jose import jwt, JWTError
from app.errors.base_exception import AppException
from app.constants.constants import *
from datetime import datetime, timedelta, timezone

def create_jwt_token(user_id, role, email) -> str:
    encode = {"authorized":"true", "user_id":user_id, "role":role, "email":email}
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRETKEY, algorithm=ALGORITHM)

def verify_jwt(request: Request) -> None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AppException(AUTH_001)
    
    token = auth_header.split(" ")[1]

    try:
        claims = jwt.decode(token, SECRETKEY, algorithms=[ALGORITHM])
    except JWTError:
        raise AppException(AUTH_002)
    
    request.state.user = claims
