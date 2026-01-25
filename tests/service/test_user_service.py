import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.service.user_service import UserService
from app.repository.user_repository import UserRepository
from app.models.user import User, UserRole, Department
from app.errors.base_exception import AppException
from app.constants.constants import *


class TestUserService(unittest.TestCase):

    def setUp(self):

        self.mock_user_repo = MagicMock(spec=UserRepository)

        self.user_service = UserService(user_repository_instance=self.mock_user_repo)

        self.sample_user = User(
            id=str(uuid4()),
            name="Manan",
            email="test@example.com",
            password="hashedpassword", 
            mobile="1234567890",
            role=UserRole.ROLEADMIN,
            department=Department.CARDIOLOGY
        )

    def tearDown(self):

        self.mock_user_repo.reset_mock()

    @patch("app.service.user_service.compare_hash_and_password")
    @patch("app.service.user_service.create_jwt_token")
    def test_get_user_by_email_and_password_success(self, mock_create_jwt, mock_compare):
 
        self.mock_user_repo.get_user_by_email.return_value = self.sample_user
        mock_compare.return_value = True
        mock_create_jwt.return_value = "fake_jwt_token"

        result = self.user_service.get_user_by_email_and_password(
            email="test@example.com",
            password="plaintextpassword"
        )

        self.mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")
        mock_compare.assert_called_once_with("plaintextpassword", self.sample_user.password)
        mock_create_jwt.assert_called_once_with(self.sample_user.id, self.sample_user.role, self.sample_user.email)

        self.assertEqual(result["token"], "fake_jwt_token")
        self.assertEqual(result["email"], self.sample_user.email)
        self.assertEqual(result["role"], self.sample_user.role)

    @patch("app.service.user_service.compare_hash_and_password")
    def test_get_user_by_email_and_password_wrong_password(self, mock_compare):

        self.mock_user_repo.get_user_by_email.return_value = self.sample_user
        mock_compare.return_value = False

        with self.assertRaises(AppException) as ctx:
            self.user_service.get_user_by_email_and_password(
                email="test@example.com",
                password="wrongpassword"
            )

        self.assertEqual(ctx.exception.error_code, USER_001)
        self.mock_user_repo.get_user_by_email.assert_called_once_with("test@example.com")

    def test_get_user_by_email_and_password_user_not_found(self):
  
        self.mock_user_repo.get_user_by_email.side_effect = AppException(USER_005)

        with self.assertRaises(AppException) as ctx:
            self.user_service.get_user_by_email_and_password(
                email="missing@example.com",
                password="any"
            )

        self.assertEqual(ctx.exception.error_code, USER_005)
        self.mock_user_repo.get_user_by_email.assert_called_once_with("missing@example.com")

    @patch("app.service.user_service.generate_hash_from_password")
    def test_add_user_success(self, mock_hash):
        self.mock_user_repo.get_user_by_email.side_effect = AppException(USER_005)
        mock_hash.return_value = "hashed_password"

        self.user_service.add_user(self.sample_user)

        self.mock_user_repo.get_user_by_email.assert_called_once_with(self.sample_user.email)
        mock_hash.assert_called_once_with("hashedpassword")
        self.assertEqual(self.sample_user.password, "hashed_password")
        self.mock_user_repo.add_user.assert_called_once_with(self.sample_user)

    def test_add_user_already_exists(self):
        self.mock_user_repo.get_user_by_email.return_value = self.sample_user

        with self.assertRaises(AppException) as ctx:
            self.user_service.add_user(self.sample_user)

        self.assertEqual(ctx.exception.error_code, USER_002)
        self.mock_user_repo.add_user.assert_not_called()

    def test_add_user_repo_unexpected_error(self):

        self.mock_user_repo.get_user_by_email.side_effect = AppException("SOME_OTHER_ERROR")

        with self.assertRaises(AppException) as ctx:
            self.user_service.add_user(self.sample_user)

        self.assertEqual(ctx.exception.error_code, SYS_001)
        self.mock_user_repo.add_user.assert_not_called()

    @patch("app.service.user_service.generate_hash_from_password")
    def test_add_user_hashing_failure(self, mock_hash):

        self.mock_user_repo.get_user_by_email.side_effect = AppException(USER_005)
        mock_hash.side_effect = Exception("hashing failed")

        with self.assertRaises(AppException) as ctx:
            self.user_service.add_user(self.sample_user)

        self.assertEqual(ctx.exception.error_code, USER_003)
        self.mock_user_repo.add_user.assert_not_called()
