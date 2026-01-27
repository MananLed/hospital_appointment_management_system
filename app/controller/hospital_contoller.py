from fastapi import APIRouter, Depends, status
from app.dependencies.authorization import require_roles
from app.service import user_service_instance
from app.dto.user import SignUpInput
from app.errors.base_exception import AppException
from app.models.user import User
from app.constants.constants import *
from app.utils.jwt import verify_jwt
from app.models.user import UserRole
from app.response.response import Response

hospital_router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(verify_jwt), Depends(require_roles(UserRole.ROLEADMIN))],
)


@hospital_router.post("/doctors")
def add_doctor(doctor_details: SignUpInput):

    if doctor_details.department is None:
        raise AppException(HOSPITAL_001)

    doctor_details.email = doctor_details.email.lower()

    new_user: User = User.model_construct(**doctor_details.model_dump())

    user_service_instance.add_user(new_user, UserRole.ROLEDOCTOR)

    return Response.success_response(
        None, "Doctor added successfully", status.HTTP_201_CREATED
    )


@hospital_router.post("/receptionists")
def add_receptionist(receptionist_details: SignUpInput):
    receptionist_details.email = receptionist_details.email.lower()
    receptionist_details.department = ""

    new_user: User = User.model_construct(**receptionist_details.model_dump())

    user_service_instance.add_user(new_user, UserRole.ROLERECEPTIONIST)

    return Response.success_response(
        None, "Receptionist added successfully", status.HTTP_201_CREATED
    )
