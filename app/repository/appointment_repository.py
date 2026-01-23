from app.errors.base_exception import AppException
from app.constants.constants import *
from typing import List

class AppointmentRepository:
    def __init__(self, ddb_connection, deserializer, table_name):
        self.deserializer = deserializer()
        self.dynamodb = ddb_connection
        self.table_name = table_name

    
    def get_all_departments(self) -> List[str]:
        statement = (
            f"SELECT * FROM {self.table_name} WHERE PK = ?"
        )

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
            department_detail = {k: self.deserializer.deserialize(v) for k, v in item.items()}
            
            departments.append(department_detail['SK']) 

        return departments