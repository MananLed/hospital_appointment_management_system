import unittest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch
from main import app
from app.constants.constants import *
from app.models.user import Department
from app.errors.base_exception import AppException


class TestAuthController(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

        self.valid_payload = {"email": "test@example.com", "password": "Valid@123"}

        self.valid_signup_payload = {
            "email": "TEST@EXAMPLE.COM",
            "password": "Valid@123",
            "name": "Manan",
            "mobile": "9876543210",
            "department": Department.CARDIOLOGY.value,
        }

    def tearDown(self):
        pass

    @patch("app.controller.auth_controller.user_service_instance")
    def test_login_success(self, mock_user_service):
        mock_user_service.get_user_by_email_and_password.return_value = {
            "token": "fake-token",
            "email": "test@example.com",
            "role": "PATIENT",
        }

        response = self.client.post("/auth/login", json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertEqual(body["status"], "Success")
        self.assertEqual(body["message"], "Login Successful")
        self.assertEqual(body["data"]["email"], "test@example.com")

        mock_user_service.get_user_by_email_and_password.assert_called_once_with(
            "test@example.com", "Valid@123"
        )

    @patch("app.controller.auth_controller.user_service_instance")
    def test_login_invalid_credentials(self, mock_user_service):

        mock_user_service.get_user_by_email_and_password.side_effect = AppException(
            USER_001
        )

        response = self.client.post("/auth/login", json=self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], USER_001)

    def test_login_invalid_password_format(self):
        payload = {"email": "test@example.com", "password": "simple123"}

        response = self.client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    def test_login_missing_password(self):
        payload = {"email": "test@example.com"}

        response = self.client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    def test_login_extra_field_not_allowed(self):
        payload = {
            "email": "test@example.com",
            "password": "Valid@123",
            "username": "hacker",
        }

        response = self.client.post("/auth/login", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    @patch("app.controller.auth_controller.user_service_instance")
    def test_signup_success(self, mock_user_service):
        response = self.client.post("/auth/signup", json=self.valid_signup_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertEqual(body["status"], "Success")
        self.assertEqual(body["message"], "Sign Up Successful")
        self.assertIsNone(body["data"])

        mock_user_service.add_user.assert_called_once()

        user_arg = mock_user_service.add_user.call_args[0][0]
        self.assertEqual(user_arg.email, "test@example.com")
        self.assertEqual(user_arg.name, "Manan")
        self.assertEqual(user_arg.mobile, "9876543210")
        self.assertIsNone(user_arg.department)

    @patch("app.controller.auth_controller.user_service_instance")
    def test_signup_user_already_exists(self, mock_user_service):
        mock_user_service.add_user.side_effect = AppException(USER_002)

        response = self.client.post("/auth/signup", json=self.valid_signup_payload)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], USER_002)

    def test_signup_invalid_password(self):
        payload = {**self.valid_signup_payload, "password": "simple123"}

        response = self.client.post("/auth/signup", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    def test_signup_invalid_mobile(self):
        payload = {**self.valid_signup_payload, "mobile": "123"}

        response = self.client.post("/auth/signup", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    def test_signup_missing_name(self):
        payload = {
            "email": "test@example.com",
            "password": "Valid@123",
            "mobile": "9876543210",
        }

        response = self.client.post("/auth/signup", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    def test_signup_extra_field(self):
        payload = {**self.valid_signup_payload, "role": "ADMIN"}

        response = self.client.post("/auth/signup", json=payload)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_CONTENT)

        body = response.json()
        self.assertEqual(body["status"], "Fail")
        self.assertEqual(body["errorcode"], SYS_001)

    @patch("app.controller.auth_controller.user_service_instance")
    def test_signup_empty_department(self, mock_user_service):
        payload = {**self.valid_signup_payload, "department": ""}

        response = self.client.post("/auth/signup", json=payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user_arg = mock_user_service.add_user.call_args[0][0]
        self.assertIsNone(user_arg.department)
