from app.repository.appointment_repository import AppointmentRepository
from typing import List
from datetime import datetime, timezone
from app.constants.constants import *
from app.utils.time_slots import get_available_slots, filter_available_slots
from app.errors.base_exception import AppException
from uuid import UUID
from datetime import date, timedelta
from app.models.appointment import Appointment, AppointmentStatus
from app.dto.appointment import TimeSlot
import json

class AppointmentService:
    def __init__(self, appointment_repository: AppointmentRepository, sns_client):
        self.appointment_repository = appointment_repository
        self.sns_client = sns_client


    def get_all_departments(self) -> List[str]:
        return self.appointment_repository.get_all_departments()
    
    def get_available_timeslots(self, id: UUID, appointment_date: date) -> List[TimeSlot]:

        today = date.today()

        max_allowed_date = today + timedelta(days=MAX_DAYS_AHEAD_BOOKING)

        if appointment_date > max_allowed_date:
            raise AppException(APPOINTMENT_009)

        occupied_timeslots = self.appointment_repository.get_occupied_timeslots(
            id,
            appointment_date
        )

        all_slots = get_available_slots(appointment_date)

        return filter_available_slots(all_slots, occupied_timeslots)
    
    
    def book_appointment(self, appointment: Appointment):
        today = date.today()

        max_allowed_date = today + timedelta(days=MAX_DAYS_AHEAD_BOOKING)

        if appointment.appointment_date > max_allowed_date:
            raise AppException(APPOINTMENT_008)

        now_utc = datetime.now(timezone.utc)
        slot_start_dt = datetime.fromisoformat(appointment.timeslot)
        if slot_start_dt <= now_utc:
            raise AppException(APPOINTMENT_004)

        all_slots = get_available_slots(appointment.appointment_date)
        slot_strings = [slot["start"] for slot in all_slots]
        if appointment.timeslot not in slot_strings:
            raise AppException(APPOINTMENT_005)
        
        patient_appointments: List[Appointment] = self.appointment_repository.get_patient_appointments(
            patient_id=appointment.patient_id,
            appointment_date=appointment.appointment_date
        )
        if len(patient_appointments) >= 3:
            raise AppException(APPOINTMENT_006)

        for existing_appointment in patient_appointments:
            if existing_appointment.department == appointment.department:
                raise AppException(APPOINTMENT_007)
            elif existing_appointment.timeslot == appointment.timeslot:
                raise AppException(APPOINTMENT_013)

        self.appointment_repository.book_appointment(appointment)

        self.sns_client.publish(
            TopicArn=APPOINTMENT_NOTIFICATION_TOPIC_ARN,
            Message=json.dumps({
                "email": appointment.email,
                "subject": "Appointment Scheduled",
                "message": f"Your appointment with Dr. {appointment.doctor_name} at {appointment.timeslot} has been scheduled successfully."
            })
        )

    def get_all_appointments_of_doctor(self, id: UUID, appointment_date: date) -> List[Appointment]:

        return self.appointment_repository.get_all_appointments_of_doctor(id, appointment_date)
    
    def get_all_appointments_of_patient(self, id: str, appointment_date: date) -> List[Appointment]:

        return self.appointment_repository.get_patient_appointments(id, appointment_date)
    
    def cancel_appointment(self, doctor_id: UUID, appointment_date: date, timeslot: str, patient_id: str | None = None) -> None:
        today = date.today()

        if appointment_date < today:
            raise AppException(APPOINTMENT_015)
        
        appointment_start = datetime.fromisoformat(timeslot)

        now_utc = datetime.now(timezone.utc)

        cancel_deadline = appointment_start - timedelta(hours=1)

        if now_utc > cancel_deadline:
            raise AppException(APPOINTMENT_016)
        
        appointments: List[Appointment] = self.appointment_repository.get_all_appointments_of_doctor(doctor_id, appointment_date, timeslot)

        if len(appointments) == 0:
            raise AppException(APPOINTMENT_017)
        
        appointment_details: Appointment = appointments[0]

        if patient_id is not None:
            if appointment_details.patient_id != patient_id:
                raise AppException(APPOINTMENT_019)

        if appointment_details.status != AppointmentStatus.BOOKED:
            raise AppException(APPOINTMENT_018)
        
        self.appointment_repository.cancel_appointment(appointment_details)

        if patient_id is not None:
            message: str = f"You have successfully cancelled your appointment with Dr. {appointment_details.doctor_name} at {appointment_details.timeslot}."
        else:
            message: str = f"Due to some unavoidable circumstances your appointment with Dr. {appointment_details.doctor_name} at {appointment_details.timeslot} has been cancelled. We apologize for the inconvinience."

        self.sns_client.publish(
            TopicArn=APPOINTMENT_NOTIFICATION_TOPIC_ARN,
            Message=json.dumps({
                "email": appointment_details.email,
                "subject": "Appointment Cancelled",
                "message": message
            })
        )

    def mark_appointment_complete(self, doctor_id: UUID, appointment_date: date, timeslot: str):
        today = date.today()

        if appointment_date > today:
            raise AppException(APPOINTMENT_021)
        
        if appointment_date == today:
            now_utc = datetime.now(timezone.utc)
            slot_start_dt = datetime.fromisoformat(timeslot)
            if slot_start_dt > now_utc:
                raise AppException(APPOINTMENT_021)
            
        appointments: List[Appointment] = self.appointment_repository.get_all_appointments_of_doctor(doctor_id, appointment_date, timeslot)

        if len(appointments) == 0:
            raise AppException(APPOINTMENT_022)
        
        appointment_details: Appointment = appointments[0]

        if appointment_details.status != AppointmentStatus.BOOKED:
            raise AppException(APPOINTMENT_024)

        self.appointment_repository.mark_appointment_complete(appointment_details)

        self.sns_client.publish(
            TopicArn=APPOINTMENT_NOTIFICATION_TOPIC_ARN,
            Message=json.dumps({
                "email": appointment_details.email,
                "subject": "Appointment Completed",
                "message": f"Your appointment with Dr. {appointment_details.doctor_name} for {appointment_details.timeslot} is completed. Hope you liked it."
            })
        )
        
        
