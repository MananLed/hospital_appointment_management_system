import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from app.models.appointment import Appointment, AppointmentStatus
from datetime import date, datetime, timedelta, timezone
from app.service.appointment_service import AppointmentService
from app.repository.appointment_repository import AppointmentRepository
from app.errors.base_exception import AppException
from app.constants.constants import *
from app.dto.appointment import TimeSlot

class TestAppointmentService(unittest.TestCase):

    def setUp(self):
        self.mock_repo = MagicMock(spec=AppointmentRepository)
        self.mock_sns_client = MagicMock()

        self.service = AppointmentService(
            appointment_repository=self.mock_repo,
            sns_client=self.mock_sns_client
        )

        self.doctor_id = uuid4()
        self.patient_id = "patient-123"

        self.future_timeslot = (
            datetime.now(timezone.utc) + timedelta(hours=2)
        ).isoformat()

        self.past_timeslot = (
        datetime.now(timezone.utc) - timedelta(hours=2)
        ).isoformat()

        self.appointment = MagicMock(spec=Appointment)
        self.appointment.id = "appt-1"
        self.appointment.patient_id = "patient-1"
        self.appointment.doctor_id = "doctor-1"
        self.appointment.department = "CARDIOLOGY"
        self.appointment.email = "test@example.com"
        self.appointment.doctor_name = "Manan"
        self.appointment.appointment_date = date.today()
        self.appointment.timeslot = (
            datetime.now(timezone.utc) + timedelta(hours=1)
        ).isoformat()

        self.appointment_cancel = MagicMock(spec=Appointment)
        self.appointment_cancel.id=uuid4()
        self.appointment_cancel.doctor_id=self.doctor_id
        self.appointment_cancel.patient_id=self.patient_id
        self.appointment_cancel.doctor_name="Dr Strange"
        self.appointment_cancel.email="patient@test.com"
        self.appointment_cancel.department="CARDIOLOGY"
        self.appointment_cancel.appointment_date=date.today()
        self.appointment_cancel.timeslot=self.future_timeslot
        self.appointment_cancel.status=AppointmentStatus.BOOKED

        self.completed_appointment = MagicMock(spec=Appointment)
        self.completed_appointment.doctor_id = self.doctor_id
        self.completed_appointment.patient_id = self.patient_id
        self.completed_appointment.doctor_name = "Dr Strange"
        self.completed_appointment.email = "patient@test.com"
        self.completed_appointment.timeslot = self.past_timeslot
        self.completed_appointment.appointment_date = date.today()
        self.completed_appointment.status = AppointmentStatus.BOOKED

    def tearDown(self):
        self.mock_repo.reset_mock()
        self.mock_sns_client.reset_mock()

    def test_get_all_departments(self):
        self.mock_repo.get_all_departments.return_value = ["CARDIOLOGY", "NEUROLOGY"]

        result = self.service.get_all_departments()

        self.assertEqual(result, ["CARDIOLOGY", "NEUROLOGY"])
        self.mock_repo.get_all_departments.assert_called_once()

    @patch("app.service.appointment_service.get_available_slots")
    @patch("app.service.appointment_service.filter_available_slots")
    def test_get_available_timeslots_success(self, mock_filter, mock_get_slots):
        doctor_id = uuid4()
        appointment_date = date.today()

        occupied_slots = ["09:00", "10:00"]
        all_slots = ["09:00", "10:00", "11:00"]
        filtered_slots = [
            TimeSlot(time="11:00", is_available=True)
        ]

        self.mock_repo.get_occupied_timeslots.return_value = occupied_slots
        mock_get_slots.return_value = all_slots
        mock_filter.return_value = filtered_slots

        result = self.service.get_available_timeslots(
            id=doctor_id,
            appointment_date=appointment_date
        )

        self.mock_repo.get_occupied_timeslots.assert_called_once_with(
            doctor_id,
            appointment_date
        )

        mock_get_slots.assert_called_once_with(appointment_date)
        mock_filter.assert_called_once_with(all_slots, occupied_slots)

        self.assertEqual(result, filtered_slots)


    def test_get_available_timeslots_date_too_far(self):
        doctor_id = uuid4()
        appointment_date = date.today() + timedelta(days=MAX_DAYS_AHEAD_BOOKING + 1)

        with self.assertRaises(AppException) as ctx:
            self.service.get_available_timeslots(
                id=doctor_id,
                appointment_date=appointment_date
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_009)

        self.mock_repo.get_occupied_timeslots.assert_not_called()

    
    def test_book_appointment_date_too_far(self):
        self.appointment.appointment_date = (
            date.today() + timedelta(days=MAX_DAYS_AHEAD_BOOKING + 1)
        )

        with self.assertRaises(AppException) as ctx:
            self.service.book_appointment(self.appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_008)
        self.mock_repo.book_appointment.assert_not_called()

    def test_book_appointment_past_timeslot(self):
        self.appointment.timeslot = (
            datetime.now(timezone.utc) - timedelta(hours=1)
        ).isoformat()

        with self.assertRaises(AppException) as ctx:
            self.service.book_appointment(self.appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_004)

    @patch("app.service.appointment_service.get_available_slots")
    def test_book_appointment_invalid_timeslot(self, mock_get_slots):
        mock_get_slots.return_value = [
            {"start": "09:00"},
            {"start": "10:00"}
        ]

        self.appointment.timeslot = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()

        with self.assertRaises(AppException) as ctx:
            self.service.book_appointment(self.appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_005)

    @patch("app.service.appointment_service.get_available_slots")
    def test_book_appointment_more_than_three(self, mock_get_slots):
        mock_get_slots.return_value = [{"start": self.appointment.timeslot}]
        self.mock_repo.get_patient_appointments.return_value = [
            MagicMock(), MagicMock(), MagicMock()
        ]

        with self.assertRaises(AppException) as ctx:
            self.service.book_appointment(self.appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_006)

    @patch("app.service.appointment_service.get_available_slots")
    def test_book_appointment_same_department(self, mock_get_slots):
        mock_get_slots.return_value = [{"start": self.appointment.timeslot}]

        existing = MagicMock()
        existing.department = self.appointment.department
        existing.timeslot = "08:00"

        self.mock_repo.get_patient_appointments.return_value = [existing]

        with self.assertRaises(AppException) as ctx:
            self.service.book_appointment(self.appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_007)

    @patch("app.service.appointment_service.get_available_slots")
    def test_book_appointment_same_timeslot(self, mock_get_slots):
        mock_get_slots.return_value = [{"start": self.appointment.timeslot}]

        existing = MagicMock()
        existing.department = "ORTHO"
        existing.timeslot = self.appointment.timeslot

        self.mock_repo.get_patient_appointments.return_value = [existing]

        with self.assertRaises(AppException) as ctx:
            self.service.book_appointment(self.appointment)

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_013)

    @patch("app.service.appointment_service.get_available_slots")
    def test_book_appointment_success(self, mock_get_slots):
        mock_get_slots.return_value = [{"start": self.appointment.timeslot}]
        self.mock_repo.get_patient_appointments.return_value = []

        self.service.book_appointment(self.appointment)

        self.mock_repo.book_appointment.assert_called_once_with(self.appointment)

        self.service.sns_client.publish.assert_called_once()
        args = self.service.sns_client.publish.call_args.kwargs

        self.assertEqual(args["TopicArn"], APPOINTMENT_NOTIFICATION_TOPIC_ARN)
        self.assertIn(self.appointment.email, args["Message"])

    def test_cancel_appointment_past_date(self):
        with self.assertRaises(AppException) as ctx:
            self.service.cancel_appointment(
                doctor_id=self.doctor_id,
                appointment_date=date.today() - timedelta(days=1),
                timeslot=self.future_timeslot
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_015)

    def test_cancel_appointment_after_deadline(self):
        late_timeslot = (
            datetime.now(timezone.utc) + timedelta(minutes=30)
        ).isoformat()

        with self.assertRaises(AppException) as ctx:
            self.service.cancel_appointment(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=late_timeslot
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_016)

    def test_cancel_appointment_not_found(self):
        self.mock_repo.get_all_appointments_of_doctor.return_value = []

        with self.assertRaises(AppException) as ctx:
            self.service.cancel_appointment(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=self.future_timeslot
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_017)

    def test_cancel_appointment_patient_mismatch(self):
        self.mock_repo.get_all_appointments_of_doctor.return_value = [self.appointment_cancel]

        with self.assertRaises(AppException) as ctx:
            self.service.cancel_appointment(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=self.future_timeslot,
                patient_id="someone-else"
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_019)
    
    def test_cancel_appointment_not_booked(self):
        self.appointment_cancel.status = AppointmentStatus.COMPLETED
        self.mock_repo.get_all_appointments_of_doctor.return_value = [self.appointment_cancel]

        with self.assertRaises(AppException) as ctx:
            self.service.cancel_appointment(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=self.future_timeslot,
                patient_id=self.patient_id
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_018)

    def test_cancel_appointment_by_patient_success(self):
        self.mock_repo.get_all_appointments_of_doctor.return_value = [self.appointment_cancel]

        self.service.cancel_appointment(
            doctor_id=self.doctor_id,
            appointment_date=date.today(),
            timeslot=self.future_timeslot,
            patient_id=self.patient_id
        )

        self.mock_repo.cancel_appointment.assert_called_once_with(self.appointment_cancel)
        self.service.sns_client.publish.assert_called_once()
    
    def test_cancel_appointment_by_doctor_success(self):
        self.mock_repo.get_all_appointments_of_doctor.return_value = [self.appointment_cancel]

        self.service.cancel_appointment(
            doctor_id=self.doctor_id,
            appointment_date=date.today(),
            timeslot=self.future_timeslot
        )

        self.mock_repo.cancel_appointment.assert_called_once_with(self.appointment_cancel)
        self.service.sns_client.publish.assert_called_once()


    def test_mark_appointment_complete_future_date(self):
        future_date = date.today() + timedelta(days=1)

        with self.assertRaises(AppException) as ctx:
            self.service.mark_appointment_complete(
                doctor_id=self.doctor_id,
                appointment_date=future_date,
                timeslot=self.future_timeslot
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_021)
    
    def test_mark_appointment_complete_today_future_time(self):
        future_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

        with self.assertRaises(AppException) as ctx:
            self.service.mark_appointment_complete(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=future_time
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_021)

    def test_mark_appointment_complete_no_appointments(self):
        self.mock_repo.get_all_appointments_of_doctor.return_value = []

        with self.assertRaises(AppException) as ctx:
            self.service.mark_appointment_complete(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=self.past_timeslot
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_022)

    def test_mark_appointment_complete_not_booked(self):
        not_booked = MagicMock(spec=Appointment)
        not_booked.status = AppointmentStatus.COMPLETED

        self.mock_repo.get_all_appointments_of_doctor.return_value = [not_booked]

        with self.assertRaises(AppException) as ctx:
            self.service.mark_appointment_complete(
                doctor_id=self.doctor_id,
                appointment_date=date.today(),
                timeslot=self.past_timeslot
            )

        self.assertEqual(ctx.exception.error_code, APPOINTMENT_024)
    
    def test_mark_appointment_complete_success(self):
        self.mock_repo.get_all_appointments_of_doctor.return_value = [
            self.completed_appointment
        ]

        self.service.mark_appointment_complete(
            doctor_id=self.doctor_id,
            appointment_date=date.today(),
            timeslot=self.past_timeslot
        )

        self.mock_repo.mark_appointment_complete.assert_called_once_with(
            self.completed_appointment
        )

        self.service.sns_client.publish.assert_called_once()






