import unittest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock
from app.models.user import Department, User
from fastapi import Request
from main import app
from uuid import uuid4
from app.utils.jwt import verify_jwt
from datetime import date, timedelta, datetime, timezone
from app.constants.constants import *
from app.models.user import UserRole


def override_verify_jwt_admin(request: Request):
    request.state.user = {"role": UserRole.ROLEADMIN}
    return request.state.user

def override_verify_jwt_patient(request: Request):
    request.state.user = {"role": UserRole.ROLEPATIENT, "email": "patient@test.com",
        "user_id": str(uuid4())}
    return request.state.user


def override_verify_jwt_doctor(request: Request):
    request.state.user = {"role": UserRole.ROLEDOCTOR}
    return request.state.user

def override_verify_jwt_receptionist(request: Request):
    request.state.user = {"role": UserRole.ROLERECEPTIONIST}
    return request.state.user

class TestAppointmentController(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.doctor_id = uuid4()

        self.future_date = date.today() + timedelta(days=1)

        self.valid_body = {
            "department": Department.CARDIOLOGY,
            "timeslot_start": (
                datetime.now(timezone.utc) + timedelta(hours=2)
            ).isoformat()
        }

    def tearDown(self):
        app.dependency_overrides = {}

    @patch("app.service.appointment_service_instance.get_all_departments")
    def test_get_all_departments_success(self, mock_get_departments):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        mock_get_departments.return_value = [
            "CARDIOLOGY",
            "NEUROLOGY",
            "ORTHOPEDICS"
        ]

        response = self.client.get("/departments")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body["status"], "Success")
        self.assertEqual(body["message"], "Departments fetched successfully")
        self.assertEqual(body["data"], mock_get_departments.return_value)

        mock_get_departments.assert_called_once()

    def test_get_all_departments_unauthorized(self):

        response = self.client.get("/departments")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["errorcode"], AUTH_001)

    @patch("app.service.user_service_instance.get_all_users_by_role")
    def test_get_all_doctors_success(self, mock_get_doctors):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        mock_doctor = MagicMock()
        mock_doctor.email = "doctor@test.com"
        mock_doctor.name = "Dr House"

        mock_get_doctors.return_value = [mock_doctor]

        response = self.client.get(
            "/doctors",
            params={"department": Department.CARDIOLOGY.value}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body["status"], "Success")
        self.assertEqual(body["message"], "Doctors fetched successfully")
        self.assertEqual(len(body["data"]), 1)

        mock_get_doctors.assert_called_once_with(
            UserRole.ROLEDOCTOR,
            Department.CARDIOLOGY
        )

    def test_get_all_doctors_missing_department(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        response = self.client.get("/doctors")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_get_all_doctors_wrong_department(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        response = self.client.get(
            "/doctors",
            params={"department": "dlfjs"}
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @patch("app.service.appointment_service_instance.get_available_timeslots")
    def test_get_available_timeslots_success(self, mock_get_timeslots):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        future_date = date.today() + timedelta(days=1)
        mock_get_timeslots.return_value = ["10:00", "10:30", "11:00"]

        response = self.client.get(
            f"/doctors/{self.doctor_id}/timeslots",
            params={"appointment_date": future_date.isoformat()}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        body = response.json()
        self.assertEqual(body["status"], "Success")
        self.assertEqual(body["message"], "Timeslots fetched successfully")
        self.assertEqual(body["data"], ["10:00", "10:30", "11:00"])

        mock_get_timeslots.assert_called_once_with(
            self.doctor_id,
            future_date
        )

    def test_get_available_timeslots_forbidden_wrong_role(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_doctor

        future_date = date.today() + timedelta(days=1)

        response = self.client.get(
            f"/doctors/{self.doctor_id}/timeslots",
            params={"appointment_date": future_date.isoformat()}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["errorcode"], AUTH_004)

    def test_get_available_timeslots_invalid_date_format(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        response = self.client.get(
            f"/doctors/{self.doctor_id}/timeslots",
            params={"appointment_date": "12-01-2026"}
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_get_available_timeslots_past_date(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        past_date = date.today() - timedelta(days=1)

        response = self.client.get(
            f"/doctors/{self.doctor_id}/timeslots",
            params={"appointment_date": past_date.isoformat()}
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @patch("app.service.appointment_service_instance.book_appointment")
    @patch("app.service.user_service_instance.get_all_users_by_role")
    def test_book_appointment_success_patient(
        self, mock_get_doctor, mock_book_appointment
    ):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        mock_get_doctor.return_value = [
            User.model_construct(
                id=str(self.doctor_id),
                name="Dr Strange",
                email="doc@test.com",
                department=Department.CARDIOLOGY,
                role=UserRole.ROLEDOCTOR
            )
        ]

        response = self.client.post(
            f"/doctors/{self.doctor_id}/appointment/book",
            params={"appointment_date": self.future_date.isoformat()},
            json=self.valid_body
        )


        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_get_doctor.assert_called_once()
        mock_book_appointment.assert_called_once()

    def test_book_appointment_forbidden_non_patient(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_doctor

        response = self.client.post(
            f"/doctors/{self.doctor_id}/appointment/book",
            params={"appointment_date": self.future_date.isoformat()},
            json=self.valid_body
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["errorcode"], AUTH_004)

    @patch("app.service.user_service_instance.get_all_users_by_role")
    def test_book_appointment_doctor_not_found(self, mock_get_doctor):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        mock_get_doctor.return_value = []

        response = self.client.post(
            f"/doctors/{self.doctor_id}/appointment/book",
            params={"appointment_date": self.future_date.isoformat()},
            json=self.valid_body
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["errorcode"], APPOINTMENT_003)

    def test_book_appointment_past_date(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        past_date = date.today() - timedelta(days=1)

        response = self.client.post(
            f"/doctors/{self.doctor_id}/appointment/book",
            params={"appointment_date": past_date.isoformat()},
            json=self.valid_body
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_book_appointment_missing_timeslot(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient

        invalid_body = {
            "department": Department.CARDIOLOGY.value
        }

        response = self.client.post(
            f"/doctors/{self.doctor_id}/appointment/book",
            params={"appointment_date": self.future_date.isoformat()},
            json=invalid_body
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    def test_get_all_appointments_invalid_date(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_receptionist

        response = self.client.get(
            f"/doctors/{self.doctor_id}/appointments",
            params={"appointment_date": "invalid-date"}
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @patch("app.service.appointment_service_instance.get_all_appointments_of_doctor")
    def test_get_all_appointments_success_receptionist(self, mock_get_appointments):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_receptionist

        mock_appointment = MagicMock()
        mock_get_appointments.return_value = [mock_appointment]

        response = self.client.get(
            f"/doctors/{self.doctor_id}/appointments",
            params={"appointment_date": date.today().isoformat()}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Appointments fetched successfully")

        mock_get_appointments.assert_called_once_with(
            self.doctor_id,
            date.fromisoformat(date.today().isoformat())
        )

    @patch("app.service.appointment_service_instance.get_all_appointments_of_patient")
    def test_get_all_appointments_of_patient_success(self, mock_service):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient
        
        mock_service.return_value = [{"id": "appt-1"}]

        response = self.client.get("/appointments", params={"appointment_date": self.future_date.isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Appointments fetched successfully", response.json()["message"])
        mock_service.assert_called_once()

    @patch("app.service.appointment_service_instance.cancel_appointment")
    def test_cancel_appointment_by_patient_success(self, mock_service):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_patient
        
        payload = {"timeslot_start": (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).isoformat()}
        response = self.client.post(f"/doctors/{self.doctor_id}/appointment/cancel", params={"appointment_date": self.future_date.isoformat()}, json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once()

    @patch("app.service.appointment_service_instance.cancel_appointment")
    def test_cancel_appointment_by_receptionist_success(self, mock_service):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_receptionist

        payload = {"timeslot_start": (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).isoformat()}
        response = self.client.post(f"/doctors/{self.doctor_id}/appointment/cancel", params={"appointment_date": self.future_date.isoformat()}, json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once()

    @patch("app.service.appointment_service_instance.mark_appointment_complete")
    def test_mark_appointment_as_complete_success(self, mock_service):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_receptionist

        payload = {"timeslot_start": (
                datetime.now(timezone.utc) - timedelta(hours=2)
            ).isoformat(),
            "appointment_date": self.future_date.isoformat()}
        response = self.client.patch(f"/doctors/{self.doctor_id}/appointment/complete", json=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_service.assert_called_once()