from app.utils.jwt import verify_jwt
from app.service import appointment_service_instance, user_service_instance
from app.models.user import User, UserRole, Department
from app.response.response import Response
from typing import List, Annotated
from app.dto.appointment import (
    BookAppointmentRequest,
    CancelAppointmentRequest,
    CompleteAppointmentRequest,
)
from app.constants.constants import *
from app.errors.base_exception import AppException
from fastapi import APIRouter, Depends, status, Query, Path, Request
from app.models.appointment import Appointment
from app.dto.appointment import DateQuery, DateQueryDoctor
from app.dependencies.authorization import require_roles
from uuid import UUID


appointment_router = APIRouter(dependencies=[Depends(verify_jwt)])


@appointment_router.get("/departments")
def get_all_departments():
    departments: List[str] = appointment_service_instance.get_all_departments()

    return Response.success_response(
        departments, "Departments fetched successfully", status.HTTP_200_OK
    )


@appointment_router.get("/doctors")
def get_all_doctors(department: Annotated[Department, Query()]):
    doctors: List[User] = user_service_instance.get_all_users_by_role(
        UserRole.ROLEDOCTOR, department
    )

    return Response.success_response(
        doctors, "Doctors fetched successfully", status.HTTP_200_OK
    )


@appointment_router.get(
    "/doctors/{id}/timeslots",
    dependencies=[Depends(require_roles(UserRole.ROLEPATIENT))],
)
def get_available_timeslots(
    id: Annotated[UUID, Path()], appointment_date: Annotated[DateQuery, Depends()]
):

    available_time_slots = appointment_service_instance.get_available_timeslots(
        id, appointment_date.appointment_date
    )

    return Response.success_response(
        available_time_slots, "Timeslots fetched successfully", status.HTTP_200_OK
    )


@appointment_router.post(
    "/doctors/{id}/appointment/book",
    dependencies=[Depends(require_roles(UserRole.ROLEPATIENT))],
)
def book_appointment(
    id: Annotated[UUID, Path()],
    appointment_date: Annotated[DateQuery, Depends()],
    body: BookAppointmentRequest,
    request: Request,
):

    claims = request.state.user

    doctor_details: List[User] = user_service_instance.get_all_users_by_role(
        UserRole.ROLEDOCTOR, body.department, id
    )

    if len(doctor_details) == 0:
        raise AppException(APPOINTMENT_003)

    chosen_doctor: User = doctor_details[0]

    new_appointment: Appointment = Appointment(
        timeslot=body.timeslot_start,
        email=claims.get("email"),
        department=body.department,
        doctor_name=chosen_doctor.name,
        doctor_id=chosen_doctor.id,
        patient_id=claims.get("user_id"),
        appointment_date=appointment_date.appointment_date,
    )

    appointment_service_instance.book_appointment(new_appointment)

    return Response.success_response(
        None, "Appointment booked successfully", status.HTTP_201_CREATED
    )


@appointment_router.get(
    "/doctors/{id}/appointments",
    dependencies=[Depends(require_roles(UserRole.ROLERECEPTIONIST))],
)
def get_all_appointments_of_doctor(
    id: Annotated[UUID, Path()], appointment_date: Annotated[DateQueryDoctor, Depends()]
):

    appointments: List[Appointment] = (
        appointment_service_instance.get_all_appointments_of_doctor(
            id, appointment_date.appointment_date
        )
    )

    return Response.success_response(
        appointments, "Appointments fetched successfully", status.HTTP_200_OK
    )


@appointment_router.get(
    "/appointments", dependencies=[Depends(require_roles(UserRole.ROLEPATIENT))]
)
def get_all_appointments_of_patient(
    appointment_date: Annotated[DateQuery, Depends()], request: Request
):

    claims = request.state.user

    appointments: List[Appointment] = (
        appointment_service_instance.get_all_appointments_of_patient(
            claims.get("user_id"), appointment_date.appointment_date
        )
    )

    return Response.success_response(
        appointments, "Appointments fetched successfully", status.HTTP_200_OK
    )


@appointment_router.post(
    "/doctors/{id}/appointment/cancel",
    dependencies=[
        Depends(require_roles(UserRole.ROLEPATIENT, UserRole.ROLERECEPTIONIST))
    ],
)
def cancel_appointment(
    id: Annotated[UUID, Path()],
    appointment_date: Annotated[DateQuery, Depends()],
    body: CancelAppointmentRequest,
    request: Request,
):

    claims = request.state.user

    if claims.get("role") == UserRole.ROLEPATIENT:
        appointment_service_instance.cancel_appointment(
            id,
            appointment_date.appointment_date,
            body.timeslot_start,
            claims.get("user_id"),
        )
    else:
        appointment_service_instance.cancel_appointment(
            id, appointment_date.appointment_date, body.timeslot_start
        )

    return Response.success_response(
        None, "Appointment cancelled successfully", status.HTTP_200_OK
    )


@appointment_router.patch(
    "/doctors/{id}/appointment/complete",
    dependencies=[Depends(require_roles(UserRole.ROLERECEPTIONIST))],
)
def mark_appointment_as_complete(
    id: Annotated[UUID, Path()], body: CompleteAppointmentRequest
):

    appointment_service_instance.mark_appointment_complete(
        id, body.appointment_date, body.timeslot_start
    )

    return Response.success_response(
        None, "Appointment marked completed successfully", status.HTTP_200_OK
    )
