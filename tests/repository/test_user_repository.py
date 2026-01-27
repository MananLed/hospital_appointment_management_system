import unittest
from unittest.mock import MagicMock
from app.repository.user_repository import UserRepository
from app.errors.base_exception import AppException
from app.constants.constants import *


class TestUserRepository(unittest.TestCase):

    def setUp(self):
        self.mock_ddb = MagicMock()
        self.mock_deserializer = MagicMock()

        self.mock_deserializer_instance = MagicMock()
        self.mock_deserializer.return_value = self.mock_deserializer_instance

        self.repo = UserRepository(
            ddb_connection=self.mock_ddb,
            deserializer=self.mock_deserializer,
            table_name="UserTable",
        )

    def tearDown(self):
        self.mock_ddb.reset_mock()
        self.mock_deserializer.reset_mock()
        self.mock_deserializer_instance.reset_mock()
        self.repo = None

    def test_get_user_by_email_success(self):
        email = "test@example.com"

        self.mock_ddb.execute_statement.return_value = {
            "Items": [{"email": {"S": email}, "name": {"S": "Manan"}}]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda attr: list(
            attr.values()
        )[0]

        user = self.repo.get_user_by_email(email)

        self.mock_ddb.execute_statement.assert_called_once_with(
            Statement="SELECT * FROM UserTable WHERE PK = ?",
            Parameters=[{"S": "USERS#EMAIL#" + email}],
        )

        self.assertEqual(user.email, email)
        self.assertEqual(user.name, "Manan")

    def test_get_user_by_email_user_not_found(self):
        self.mock_ddb.execute_statement.return_value = {"Items": []}

        with self.assertRaises(AppException) as ctx:
            self.repo.get_user_by_email("missing@example.com")

        exc = ctx.exception
        self.assertEqual(exc.error_code, USER_005)

    def test_get_user_by_email_ddb_exception(self):
        self.mock_ddb.execute_statement.side_effect = Exception("DDB failure")

        with self.assertRaises(AppException) as ctx:
            self.repo.get_user_by_email("test@example.com")

        exc = ctx.exception
        self.assertEqual(exc.error_code, USER_004)

    def test_add_user_success(self):

        mock_user = MagicMock()
        mock_user.id = "123"
        mock_user.email = "test@example.com"
        mock_user.name = "Manan"
        mock_user.mobile = "9999999999"
        mock_user.password = "hashed_password"

        mock_role = MagicMock()
        mock_role.value = "admin"
        mock_user.role = mock_role

        mock_department = MagicMock()
        mock_department.value = 1
        mock_user.department = mock_department

        result = self.repo.add_user(mock_user)

        self.assertIsNone(result)

        self.mock_ddb.execute_transaction.assert_called_once()

        call_args = self.mock_ddb.execute_transaction.call_args[1]
        self.assertIn("TransactStatements", call_args)
        self.assertEqual(len(call_args["TransactStatements"]), 2)

    def test_add_user_ddb_failure(self):
        mock_user = MagicMock()
        mock_user.id = "123"
        mock_user.email = "fail@example.com"
        mock_user.name = "Fail User"
        mock_user.mobile = "0000000000"
        mock_user.password = "password"

        mock_role = MagicMock()
        mock_role.value = "user"
        mock_user.role = mock_role

        mock_user.department = None

        self.mock_ddb.execute_transaction.side_effect = Exception("DDB error")

        with self.assertRaises(AppException) as ctx:
            self.repo.add_user(mock_user)

        exc = ctx.exception
        self.assertEqual(exc.error_code, USER_006)

    def _mock_ddb_user_item(self, email="test@example.com"):
        return {"email": {"S": email}, "name": {"S": "Manan"}}

    def test_get_all_users_by_role_without_department(self):

        role = MagicMock()
        role.value = "admin"

        self.mock_ddb.execute_statement.return_value = {
            "Items": [self._mock_ddb_user_item()]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        users = self.repo.get_all_users_by_role(role)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, "test@example.com")

        self.mock_ddb.execute_statement.assert_called_once()

    def test_get_all_users_by_role_with_department_and_id(self):
        role = MagicMock()
        role.value = "doctor"

        department = MagicMock()
        department.value = 2

        user_id = "123"

        self.mock_ddb.execute_statement.return_value = {
            "Items": [self._mock_ddb_user_item("doc@example.com")]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        users = self.repo.get_all_users_by_role(
            role=role, department=department, id=user_id
        )

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, "doc@example.com")

        call_args = self.mock_ddb.execute_statement.call_args[1]
        self.assertIn("begins_with", call_args["Statement"])

    def test_get_all_users_by_role_with_department_only(self):

        role = MagicMock()
        role.value = "receptionist"

        department = MagicMock()
        department.value = 3

        self.mock_ddb.execute_statement.return_value = {
            "Items": [self._mock_ddb_user_item("receptionist@example.com")]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        users = self.repo.get_all_users_by_role(role=role, department=department)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, "receptionist@example.com")

        call_args = self.mock_ddb.execute_statement.call_args[1]
        self.assertIn("begins_with", call_args["Statement"])

    def test_get_all_users_by_role_ddb_failure(self):

        role = MagicMock()
        role.value = "admin"

        self.mock_ddb.execute_statement.side_effect = Exception("DDB down")

        with self.assertRaises(AppException) as ctx:
            self.repo.get_all_users_by_role(role)

        exc = ctx.exception
        self.assertEqual(exc.error_code, USER_007)
