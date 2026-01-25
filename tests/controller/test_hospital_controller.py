import unittest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch
from main import app
from app.constants.constants import *
from app.models.user import UserRole
from app.models.user import Department
from fastapi import Request
from app.utils.jwt import verify_jwt
import app.controller.hospital_contoller as hospital_controller

def override_verify_jwt_admin(request: Request):
    request.state.user = {"role": UserRole.ROLEADMIN}
    return request.state.user

def override_verify_jwt_doctor(request: Request):
    request.state.user = {"role": UserRole.ROLEDOCTOR}
    return request.state.user

class TestHospitalController(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.valid_payload = {
            "email": "DOCTOR@HOSPITAL.COM",
            "password": "Valid@123",
            "name": "Dr. Strange",
            "mobile": "9876543210",
            "department": Department.CARDIOLOGY.value
        }

        self.valid_payload_receptionist = {
            "email": "receptionist@gmail.com",
            "password": "Reception@123",
            "name": "dfjls dlfj",
            "mobile": "8769878798"
        }

        self.role_dependency = hospital_controller.require_roles(UserRole.ROLEADMIN)

    def tearDown(self):
        app.dependency_overrides = {}

    @patch("app.service.user_service_instance.add_user")
    def test_add_doctor_success_admin(self, mock_add_user):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        response = self.client.post("/admin/doctors", json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_add_user.assert_called_once()

        args, _ = mock_add_user.call_args
        self.assertEqual(args[1], UserRole.ROLEDOCTOR)

    def test_add_doctor_forbidden_non_admin(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_doctor

        response = self.client.post("/admin/doctors", json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["errorcode"], AUTH_004)


    def test_add_doctor_missing_department(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        payload = self.valid_payload.copy()
        payload["department"] = None

        response = self.client.post("/admin/doctors", json=payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["errorcode"], HOSPITAL_001)

    @patch("app.service.user_service_instance.add_user")
    def test_add_receptionist_success_admin(self, mock_add_user):

        app.dependency_overrides[verify_jwt] = override_verify_jwt_admin

        response = self.client.post("/admin/receptionists", json=self.valid_payload_receptionist)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_add_user.assert_called_once()

        args, _ = mock_add_user.call_args
        self.assertEqual(args[1], UserRole.ROLERECEPTIONIST)

    def test_add_receptionist_forbidden_non_admin(self):
        app.dependency_overrides[verify_jwt] = override_verify_jwt_doctor

        response = self.client.post("/admin/receptionists", json=self.valid_payload_receptionist)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()["errorcode"], AUTH_004)