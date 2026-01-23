from app.repository.appointment_repository import AppointmentRepository
from typing import List

class AppointmentService:
    def __init__(self, appointment_repository: AppointmentRepository):
        self.appointment_repository = appointment_repository


    def get_all_departments(self) -> List[str]:
        return self.appointment_repository.get_all_departments()