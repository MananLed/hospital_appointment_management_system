from app.errors.base_exception import AppException
from app.constants.constants import *
from typing import List
from uuid import UUID
from app.models.appointment import Appointment, AppointmentStatus
from app.utils.time_slots import calculate_expires_at
from botocore.exceptions import ClientError
from datetime import date


class AppointmentRepository:
    def __init__(self, ddb_connection, deserializer, table_name):
        self.deserializer = deserializer()
        self.dynamodb = ddb_connection
        self.table_name = table_name

    def get_all_departments(self) -> List[str]:
        statement = f"SELECT * FROM {self.table_name} WHERE PK = ?"

        try:
            response = self.dynamodb.execute_statement(
                Statement=statement,
                Parameters=[{"S": "DEPARTMENTS"}],
            )
        except Exception:
            raise AppException(APPOINTMENT_001)

        items = response["Items"]

        departments: List[str] = []

        for item in items:
            department_detail = {
                k: self.deserializer.deserialize(v) for k, v in item.items()
            }

            departments.append(department_detail["SK"])

        return departments

    def get_occupied_timeslots(self, id: UUID, appointment_date: date) -> List[str]:
        try:
            response = self.dynamodb.execute_statement(
                Statement=f"""
                        SELECT SK FROM {self.table_name}
                        WHERE PK = ?
                    """,
                Parameters=[
                    {"S": f"DOCTOR#UUID#{str(id)}#DATE#{appointment_date.isoformat()}"}
                ],
            )
        except:
            raise AppException(APPOINTMENT_002)

        items = response["Items"]

        occupied_timeslots: List[str] = []

        for item in items:
            occupied_timeslots_details = {
                k: self.deserializer.deserialize(v) for k, v in item.items()
            }

            if not occupied_timeslots_details["SK"].startswith("TIME#"):
                continue

            occupied_timeslots.append(
                occupied_timeslots_details["SK"].replace("TIME#", "", 1)
            )

        return occupied_timeslots

    def get_patient_appointments(
        self, patient_id: str, appointment_date: date
    ) -> List[Appointment]:
        pk = f"PATIENT#UUID#{patient_id}"
        sk = f"DATE#{appointment_date.isoformat()}"

        try:
            response = self.dynamodb.execute_statement(
                Statement=f"""
                SELECT *
                FROM {self.table_name}
                WHERE PK = ? AND begins_with(SK, ?)
                """,
                Parameters=[{"S": pk}, {"S": sk}],
            )
        except:
            raise AppException(APPOINTMENT_010)

        items = response.get("Items", [])
        appointments: List[Appointment] = []

        for item in items:
            row = {k: self.deserializer.deserialize(v) for k, v in item.items()}

            appointment: Appointment = Appointment.model_construct(**row)

            appointments.append(appointment)

        return appointments

    def book_appointment(self, appointment: Appointment) -> None:
        expires_at: int = calculate_expires_at()

        doctor_pk = f"DOCTOR#UUID#{appointment.doctor_id}#DATE#{appointment.appointment_date.isoformat()}"
        doctor_sk = f"TIME#{appointment.timeslot}"

        patient_pk = f"PATIENT#UUID#{appointment.patient_id}"
        patient_sk = f"DATE#{appointment.appointment_date.isoformat()}#DEPARTMENT#{appointment.department}#DOCTOR#UUID#{appointment.doctor_id}#TIME#{appointment.timeslot}"

        common_parameters = [
            {"S": appointment.id},
            {"S": appointment.timeslot},
            {"S": appointment.email},
            {"S": appointment.status.value},
            {"S": appointment.department},
            {"S": appointment.doctor_name},
            {"S": appointment.doctor_id},
            {"S": appointment.patient_id},
            {"S": appointment.appointment_date.isoformat()},
            {"S": appointment.created_at.isoformat()},
            {"N": str(expires_at)},
        ]

        statement: str = f"""
            INSERT INTO "{self.table_name}" 
            VALUE {{
                'PK': ?, 'SK': ?, 'id': ?, 'timeslot': ?, 'email': ?, 
                'status': ?, 'department': ?, 'doctor_name': ?, 'doctor_id': ?,
                'patient_id': ?, 'date': ?, 'created_at': ?, 'expires_at': ?
            }}
        """

        try:
            self.dynamodb.execute_transaction(
                TransactStatements=[
                    {
                        "Statement": statement,
                        "Parameters": [{"S": doctor_pk}, {"S": doctor_sk}]
                        + common_parameters,
                    },
                    {
                        "Statement": statement,
                        "Parameters": [{"S": patient_pk}, {"S": patient_sk}]
                        + common_parameters,
                    },
                ]
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "TransactionCanceledException":
                reasons = e.response.get("CancellationReasons", [])
                if any(r.get("Code") == "ConditionalCheckFailed" for r in reasons):
                    raise AppException(APPOINTMENT_011)

            raise AppException(APPOINTMENT_012)

    def get_all_appointments_of_doctor(
        self, id: UUID, appointment_date: date, timeslot: str | None = None
    ) -> List[Appointment]:
        pk = f"DOCTOR#UUID#{str(id)}#DATE#{appointment_date.isoformat()}"

        if timeslot is not None:
            sk = f"TIME#{timeslot}"

        try:
            if timeslot is None:
                response = self.dynamodb.execute_statement(
                    Statement=f"""
                    SELECT *
                    FROM {self.table_name}
                    WHERE PK = ?
                    """,
                    Parameters=[{"S": pk}],
                )
            else:
                response = self.dynamodb.execute_statement(
                    Statement=f"""
                    SELECT *
                    FROM {self.table_name}
                    WHERE PK = ? and SK = ?
                    """,
                    Parameters=[{"S": pk}, {"S": sk}],
                )
        except:
            raise AppException(APPOINTMENT_014)

        items = response.get("Items", [])
        appointments: List[Appointment] = []

        for item in items:
            row = {k: self.deserializer.deserialize(v) for k, v in item.items()}

            appointment: Appointment = Appointment.model_construct(**row)

            appointments.append(appointment)

        return appointments

    def cancel_appointment(self, appointment: Appointment) -> None:

        doctor_pk = (
            f"DOCTOR#UUID#{appointment.doctor_id}#DATE#{appointment.appointment_date}"
        )
        doctor_sk = f"TIME#{appointment.timeslot}"

        patient_pk = f"PATIENT#UUID#{appointment.patient_id}"
        patient_sk = f"DATE#{appointment.appointment_date}#DEPARTMENT#{appointment.department}#DOCTOR#UUID#{appointment.doctor_id}#TIME#{appointment.timeslot}"

        statement = f"DELETE FROM {self.table_name} WHERE PK = ? AND SK = ?"

        try:
            self.dynamodb.execute_transaction(
                TransactStatements=[
                    {
                        "Statement": statement,
                        "Parameters": [{"S": doctor_pk}, {"S": doctor_sk}],
                    },
                    {
                        "Statement": statement,
                        "Parameters": [{"S": patient_pk}, {"S": patient_sk}],
                    },
                ]
            )
        except:
            raise AppException(APPOINTMENT_020)

    def mark_appointment_complete(self, appointment: Appointment) -> None:
        doctor_pk = (
            f"DOCTOR#UUID#{appointment.doctor_id}#DATE#{appointment.appointment_date}"
        )
        doctor_sk = f"TIME#{appointment.timeslot}"

        patient_pk = f"PATIENT#UUID#{appointment.patient_id}"
        patient_sk = f"DATE#{appointment.appointment_date}#DEPARTMENT#{appointment.department}#DOCTOR#UUID#{appointment.doctor_id}#TIME#{appointment.timeslot}"

        statement = f"UPDATE {self.table_name} SET status = ? WHERE PK = ? AND SK = ?"

        try:
            self.dynamodb.execute_transaction(
                TransactStatements=[
                    {
                        "Statement": statement,
                        "Parameters": [
                            {"S": AppointmentStatus.COMPLETED.value},
                            {"S": doctor_pk},
                            {"S": doctor_sk},
                        ],
                    },
                    {
                        "Statement": statement,
                        "Parameters": [
                            {"S": AppointmentStatus.COMPLETED.value},
                            {"S": patient_pk},
                            {"S": patient_sk},
                        ],
                    },
                ]
            )
        except:
            raise AppException(APPOINTMENT_023)
