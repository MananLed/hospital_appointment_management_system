from pydantic import BaseModel, ConfigDict, Field, EmailStr
from enum import Enum
from uuid import uuid4


class UserRole(str, Enum):
    ROLEADMIN = "admin"
    ROLEDOCTOR = "officer"
    ROLERECEPTIONIST = "receptionist"
    ROLEPATIENT = "patient"

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)

    id: str = Field(alias="id", default_factory=lambda: str(uuid4()))
    email: EmailStr = Field(alias="email")
    password: str = Field(alias="password", exclude=True)
    name: str = Field(alias="name")
    mobile: str = Field(alias="mobile")
    department: str | None = Field(alias="department", default=None)
    role: UserRole = Field(default=UserRole.ROLEPATIENT, alias="role")