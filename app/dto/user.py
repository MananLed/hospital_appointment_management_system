from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")

class LoginInput(BaseModel):

    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    email: EmailStr = Field(alias="email")
    password: str = Field(alias="password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Invalid Details"
            )
        return v
    

class SignUpInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True, validate_assignment=True)

    email: EmailStr = Field(alias="email")
    password: str = Field(alias="password")
    name: str = Field(alias="name")
    mobile: str = Field(alias="mobile", pattern=r"^[+]{1}(?:[0-9\-\(\)\/\.]\s?){6,15}[0-9]{1}$")
    department: str | None = Field(default=None)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )
        return v
    

# from fastapi import FastAPI, Request, status
# from fastapi.exceptions import RequestValidationError
# from fastapi.responses import JSONResponse

# app = FastAPI()

# @app.exception_handler(RequestValidationError)
# async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
#     # 1. Access detailed errors
#     errors = exc.errors()
    
#     # 2. Extract specific field and custom message
#     # In V2, 'loc' often starts with ('body', 'field_name')
#     custom_details = []
#     for error in errors:
#         field = ".".join(map(str, error["loc"][1:])) if len(error["loc"]) > 1 else error["loc"][0]
#         custom_details.append({
#             "field": field,
#             "error_type": error["type"],
#             "custom_message": f"Hey! The input for '{field}' is invalid. System says: {error['msg']}"
#         })

#     # 3. Return a custom JSON response
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={
#             "status": "error",
#             "message": "Validation failed for your hospital request",
#             "details": custom_details,
#             "original_payload": exc.body  # Optional: helpful for debugging in dev
#         }
#     )
