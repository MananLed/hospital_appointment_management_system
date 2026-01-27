import unittest
from unittest.mock import MagicMock
from app.repository.appointment_repository import AppointmentRepository
from app.models.appointment import AppointmentStatus
from datetime import datetime
from botocore.exceptions import ClientError
from app.errors.base_exception import AppException
from app.constants.constants import *
from uuid import uuid4
from datetime import date


class TestAppointmentRepository(unittest.TestCase):

    def setUp(self):
        self.mock_ddb = MagicMock()
        self.mock_deserializer = MagicMock()

        self.mock_deserializer_instance = MagicMock()
        self.mock_deserializer.return_value = self.mock_deserializer_instance

        self.repo = AppointmentRepository(
            ddb_connection=self.mock_ddb,
            deserializer=self.mock_deserializer,
            table_name="AppointmentTable",
        )

    def tearDown(self):
        self.mock_ddb.reset_mock()
        self.mock_deserializer.reset_mock()
        self.mock_deserializer_instance.reset_mock()
        self.repo = None

    def test_get_all_departments_success(self):
        self.mock_ddb.execute_statement.return_value = {
            "Items": [
                {"SK": {"S": "CARDIOLOGY"}},
                {"SK": {"S": "ORTHOPEDICS"}},
            ]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        departments = self.repo.get_all_departments()

        self.assertEqual(departments, ["CARDIOLOGY", "ORTHOPEDICS"])

        self.mock_ddb.execute_statement.assert_called_once_with(
            Statement="SELECT * FROM AppointmentTable WHERE PK = ?",
            Parameters=[{"S": "DEPARTMENTS"}],
        )

    def test_get_all_departments_ddb_failure(self):
        self.mock_ddb.execute_statement.side_effect = Exception("DDB down")

        with self.assertRaises(AppException) as ctx:
            self.repo.get_all_departments()

        exc = ctx.exception
        self.assertEqual(exc.error_code, APPOINTMENT_001)

    def test_get_occupied_timeslots_success(self):
        doctor_id = uuid4()
        appointment_date = date(2024, 1, 15)

        self.mock_ddb.execute_statement.return_value = {
            "Items": [
                {"SK": {"S": "TIME#09:00"}},
                {"SK": {"S": "TIME#10:30"}},
                {"SK": {"S": "METADATA#SOMETHING"}},
            ]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        result = self.repo.get_occupied_timeslots(
            id=doctor_id, appointment_date=appointment_date
        )

        self.assertEqual(result, ["09:00", "10:30"])

        self.mock_ddb.execute_statement.assert_called_once()

        called_args = self.mock_ddb.execute_statement.call_args.kwargs

        self.assertIn("SELECT SK FROM AppointmentTable", called_args["Statement"])
        self.assertIn("WHERE PK = ?", called_args["Statement"])

        self.assertEqual(
            called_args["Parameters"],
            [
                {
                    "S": f"DOCTOR#UUID#{str(doctor_id)}#DATE#{appointment_date.isoformat()}"
                }
            ],
        )

    def test_get_occupied_timeslots_empty(self):
        doctor_id = uuid4()
        appointment_date = date.today()

        self.mock_ddb.execute_statement.return_value = {"Items": []}

        result = self.repo.get_occupied_timeslots(
            id=doctor_id, appointment_date=appointment_date
        )

        self.assertEqual(result, [])

    def test_get_occupied_timeslots_ddb_failure(self):
        doctor_id = uuid4()
        appointment_date = date.today()

        self.mock_ddb.execute_statement.side_effect = Exception("DDB failure")

        with self.assertRaises(AppException) as ctx:
            self.repo.get_occupied_timeslots(
                id=doctor_id, appointment_date=appointment_date
            )

        exc = ctx.exception
        self.assertEqual(exc.error_code, APPOINTMENT_002)

    def test_get_patient_appointments_success(self):
        patient_id = "patient-123"
        appointment_date = date(2024, 1, 15)

        self.mock_ddb.execute_statement.return_value = {
            "Items": [
                {
                    "id": {"S": "appt-1"},
                    "patient_id": {"S": patient_id},
                    "doctor_id": {"S": "doc-1"},
                    "status": {"S": "CONFIRMED"},
                    "date": {"S": appointment_date.isoformat()},
                },
                {
                    "id": {"S": "appt-2"},
                    "patient_id": {"S": patient_id},
                    "doctor_id": {"S": "doc-2"},
                    "status": {"S": "PENDING"},
                    "date": {"S": appointment_date.isoformat()},
                },
            ]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        result = self.repo.get_patient_appointments(
            patient_id=patient_id, appointment_date=appointment_date
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "appt-1")
        self.assertEqual(result[1].id, "appt-2")

        self.mock_ddb.execute_statement.assert_called_once()

        called_args = self.mock_ddb.execute_statement.call_args.kwargs

        self.assertIn("SELECT *", called_args["Statement"])
        self.assertIn("WHERE PK = ? AND begins_with(SK, ?)", called_args["Statement"])

        self.assertEqual(
            called_args["Parameters"],
            [
                {"S": f"PATIENT#UUID#{patient_id}"},
                {"S": f"DATE#{appointment_date.isoformat()}"},
            ],
        )

    def test_get_patient_appointments_empty(self):
        self.mock_ddb.execute_statement.return_value = {"Items": []}

        result = self.repo.get_patient_appointments(
            patient_id="patient-123", appointment_date=date(2024, 1, 15)
        )

        self.assertEqual(result, [])
        self.mock_ddb.execute_statement.assert_called_once()

    def test_get_patient_appointments_ddb_failure(self):
        self.mock_ddb.execute_statement.side_effect = Exception("DDB error")

        with self.assertRaises(AppException) as ctx:
            self.repo.get_patient_appointments(
                patient_id="patient-123", appointment_date=date(2024, 1, 15)
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_010)

    def _build_appointment(self):
        return MagicMock(
            id=str(uuid4()),
            timeslot="09:00",
            email="test@example.com",
            status=AppointmentStatus.BOOKED,
            department="CARDIOLOGY",
            doctor_name="Dr Strange",
            doctor_id=str(uuid4()),
            patient_id=str(uuid4()),
            appointment_date=date(2024, 1, 15),
            created_at=datetime(2024, 1, 10, 10, 0, 0),
        )

    def test_book_appointment_success(self):
        appointment = self._build_appointment()

        self.mock_ddb.execute_transaction.return_value = None

        self.repo.book_appointment(appointment)

        self.mock_ddb.execute_transaction.assert_called_once()

        args = self.mock_ddb.execute_transaction.call_args.kwargs
        self.assertIn("TransactStatements", args)
        self.assertEqual(len(args["TransactStatements"]), 2)

    def test_book_appointment_slot_already_booked(self):
        appointment = self._build_appointment()

        error_response = {
            "Error": {"Code": "TransactionCanceledException"},
            "CancellationReasons": [{"Code": "ConditionalCheckFailed"}],
        }

        self.mock_ddb.execute_transaction.side_effect = ClientError(
            error_response=error_response, operation_name="ExecuteTransaction"
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.book_appointment(appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_011)

    def test_book_appointment_generic_ddb_error(self):
        appointment = self._build_appointment()

        error_response = {"Error": {"Code": "InternalServerError"}}

        self.mock_ddb.execute_transaction.side_effect = ClientError(
            error_response=error_response, operation_name="ExecuteTransaction"
        )

        with self.assertRaises(AppException) as ctx:
            self.repo.book_appointment(appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_012)

    def test_get_all_appointments_of_doctor_without_timeslot(self):
        doctor_id = uuid4()
        appointment_date = date(2024, 1, 15)

        self.mock_ddb.execute_statement.return_value = {
            "Items": [
                {
                    "id": {"S": "appt-1"},
                    "doctor_id": {"S": str(doctor_id)},
                    "timeslot": {"S": "09:00"},
                    "date": {"S": appointment_date.isoformat()},
                },
                {
                    "id": {"S": "appt-2"},
                    "doctor_id": {"S": str(doctor_id)},
                    "timeslot": {"S": "10:00"},
                    "date": {"S": appointment_date.isoformat()},
                },
            ]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        result = self.repo.get_all_appointments_of_doctor(
            id=doctor_id, appointment_date=appointment_date
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "appt-1")
        self.assertEqual(result[1].id, "appt-2")

        self.mock_ddb.execute_statement.assert_called_once()

        args = self.mock_ddb.execute_statement.call_args.kwargs
        self.assertEqual(
            args["Parameters"],
            [
                {
                    "S": f"DOCTOR#UUID#{str(doctor_id)}#DATE#{appointment_date.isoformat()}"
                }
            ],
        )

    def test_get_all_appointments_of_doctor_with_timeslot(self):
        doctor_id = uuid4()
        appointment_date = date(2024, 1, 15)
        timeslot = "09:00"

        self.mock_ddb.execute_statement.return_value = {
            "Items": [
                {
                    "id": {"S": "appt-1"},
                    "doctor_id": {"S": str(doctor_id)},
                    "timeslot": {"S": timeslot},
                    "date": {"S": appointment_date.isoformat()},
                }
            ]
        }

        self.mock_deserializer_instance.deserialize.side_effect = lambda v: list(
            v.values()
        )[0]

        result = self.repo.get_all_appointments_of_doctor(
            id=doctor_id, appointment_date=appointment_date, timeslot=timeslot
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].timeslot, timeslot)

        self.mock_ddb.execute_statement.assert_called_once()

        args = self.mock_ddb.execute_statement.call_args.kwargs
        self.assertEqual(
            args["Parameters"],
            [
                {
                    "S": f"DOCTOR#UUID#{str(doctor_id)}#DATE#{appointment_date.isoformat()}"
                },
                {"S": f"TIME#{timeslot}"},
            ],
        )

    def test_get_all_appointments_of_doctor_ddb_failure(self):
        self.mock_ddb.execute_statement.side_effect = Exception("DDB error")

        with self.assertRaises(AppException) as ctx:
            self.repo.get_all_appointments_of_doctor(
                id=uuid4(), appointment_date=date(2024, 1, 15)
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_014)

    def test_cancel_appointment_success(self):
        appointment = MagicMock()
        appointment.doctor_id = "doctor-123"
        appointment.patient_id = "patient-456"
        appointment.timeslot = "09:00"
        appointment.department = "CARDIOLOGY"
        appointment.appointment_date = date(2024, 1, 15)

        self.repo.cancel_appointment(appointment)

        self.mock_ddb.execute_transaction.assert_called_once()

        args = self.mock_ddb.execute_transaction.call_args.kwargs
        transact_statements = args["TransactStatements"]

        self.assertEqual(len(transact_statements), 2)

        self.assertEqual(
            transact_statements[0]["Parameters"],
            [
                {
                    "S": f"DOCTOR#UUID#{appointment.doctor_id}#DATE#{appointment.appointment_date}"
                },
                {"S": f"TIME#{appointment.timeslot}"},
            ],
        )

        self.assertEqual(
            transact_statements[1]["Parameters"],
            [
                {"S": f"PATIENT#UUID#{appointment.patient_id}"},
                {
                    "S": (
                        f"DATE#{appointment.appointment_date}"
                        f"#DEPARTMENT#{appointment.department}"
                        f"#DOCTOR#UUID#{appointment.doctor_id}"
                        f"#TIME#{appointment.timeslot}"
                    )
                },
            ],
        )

    def test_cancel_appointment_ddb_failure(self):
        appointment = MagicMock()
        appointment.doctor_id = "doctor-123"
        appointment.patient_id = "patient-456"
        appointment.timeslot = "09:00"
        appointment.department = "CARDIOLOGY"
        appointment.appointment_date = date(2024, 1, 15)

        self.mock_ddb.execute_transaction.side_effect = Exception("DDB down")

        with self.assertRaises(AppException) as ctx:
            self.repo.cancel_appointment(appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_020)

    def test_mark_appointment_complete_success(self):
        appointment = MagicMock()
        appointment.doctor_id = "doctor-123"
        appointment.patient_id = "patient-456"
        appointment.timeslot = "09:00"
        appointment.department = "CARDIOLOGY"
        appointment.appointment_date = date(2024, 1, 15)

        self.repo.mark_appointment_complete(appointment)

        self.mock_ddb.execute_transaction.assert_called_once()

        args = self.mock_ddb.execute_transaction.call_args.kwargs
        transact_statements = args["TransactStatements"]

        self.assertEqual(len(transact_statements), 2)

        self.assertEqual(
            transact_statements[0]["Parameters"],
            [
                {"S": AppointmentStatus.COMPLETED.value},
                {
                    "S": f"DOCTOR#UUID#{appointment.doctor_id}#DATE#{appointment.appointment_date}"
                },
                {"S": f"TIME#{appointment.timeslot}"},
            ],
        )

        self.assertEqual(
            transact_statements[1]["Parameters"],
            [
                {"S": AppointmentStatus.COMPLETED.value},
                {"S": f"PATIENT#UUID#{appointment.patient_id}"},
                {
                    "S": (
                        f"DATE#{appointment.appointment_date}"
                        f"#DEPARTMENT#{appointment.department}"
                        f"#DOCTOR#UUID#{appointment.doctor_id}"
                        f"#TIME#{appointment.timeslot}"
                    )
                },
            ],
        )

    def test_mark_appointment_complete_ddb_failure(self):
        appointment = MagicMock()
        appointment.doctor_id = "doctor-123"
        appointment.patient_id = "patient-456"
        appointment.timeslot = "09:00"
        appointment.department = "CARDIOLOGY"
        appointment.appointment_date = date(2024, 1, 15)

        self.mock_ddb.execute_transaction.side_effect = Exception("DDB down")

        with self.assertRaises(AppException) as ctx:
            self.repo.mark_appointment_complete(appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_023)
