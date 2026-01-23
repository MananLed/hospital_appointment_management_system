from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import TypedDict
from app.models.user import UserRole, Department
import re

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")
MOBILE_REGEX = re.compile(r"^[6-9][0-9]{9}$")

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
    mobile: str = Field(alias="mobile")
    department: Department | None = Field(alias="department", default=None)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if not PASSWORD_REGEX.match(v):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )
        return v

    @field_validator("mobile")
    @classmethod
    def validate_mobile_number(cls, v: str):
        if not MOBILE_REGEX.match(v):
            raise ValueError(
                "Password must contain uppercase, lowercase, digit, and special character"
            )
        return v

class AuthResponse(TypedDict):
    token: str
    email: str
    role: UserRole