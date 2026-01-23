from app.utils.jwt import verify_jwt
from app.service import appointment_service_instance, user_service_instance
from app.models.user import User, UserRole, Department
from app.response.response import Response
from typing import List, Annotated
from app.utils.time_slots import get_available_slots
from fastapi import APIRouter, Depends, status, Query, Path
from app.dto.appointment import DateQuery
from app.dependencies.authorization import require_roles
from uuid import UUID


appointment_router = APIRouter(dependencies=[Depends(verify_jwt)])


@appointment_router.get("/departments")
def get_all_departments():
    departments: List[str] =  appointment_service_instance.get_all_departments()

    return Response.success_response(departments, "Departments fetched successfully", status.HTTP_200_OK)


@appointment_router.get("/doctors")
def get_all_doctors(department: Annotated[Department, Query()]):
    doctors: List[User] = user_service_instance.get_all_users_by_role(UserRole.ROLEDOCTOR, department)

    return Response.success_response(doctors, "Doctors fetched successfully", status.HTTP_200_OK) 


@appointment_router.get("/doctors/{id}/timeslots")
def get_available_timeslots(id: Annotated[UUID, Path()], department: Annotated[Department, Query()], appointment_date: Annotated[DateQuery, Depends()]):
    return Response.success_response(get_available_slots(appointment_date.appointment_date), "Timeslots fetched successfully", status.HTTP_200_OK)

@appointment_router.post("/doctors/{id}/appointment/book", dependencies=[Depends(require_roles(UserRole.ROLEPATIENT))])
def book_appointment(id: Annotated[UUID, Path()], department: Annotated[Department, Query()], date: Annotated[DateQuery, Depends()]):
    pass 

@appointment_router.post("appointment/{id}/cancel")
def cancel_appointment():
    pass 

@appointment_router.patch("/appointment/{id}/complete")
def mark_appointment_as_complete():
    pass

