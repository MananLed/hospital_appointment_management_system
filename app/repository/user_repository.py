from app.models.user import User
from app.constants.constants import * 
from app.errors.base_exception import AppException
from app.models.user import User, UserRole, Department
from typing import List


class UserRepository:
    def __init__(self, ddb_connection, deserializer, table_name):
        self.deserializer = deserializer()
        self.dynamodb = ddb_connection
        self.table_name = table_name    

    def get_user_by_email(self, email: str) -> User:
        statement = (
            f"SELECT * FROM {self.table_name} WHERE PK = ? AND begins_with(SK, ?)"
        )

        try:
            response = self.dynamodb.execute_statement(
                Statement=statement,
                Parameters=[{"S": "USERS"}, {"S": ("EMAIL#" + email)}],
            )
        except Exception:
            raise AppException(USER_004)

        items = response["Items"]

        if len(items) == 0:
            raise AppException(USER_005)

        for item in items:
            user_details = {
                k: self.deserializer.deserialize(v) for k, v in item.items()
            }

        user: User = User.model_construct(**user_details)

        return user
            
            
    def add_user(self, new_user: User) -> None:
        statement = f"INSERT INTO {self.table_name} VALUE {{'PK': ?, 'SK': ?, 'id': ?, 'email': ?, 'name': ?, 'mobile': ?, 'password': ?, 'role': ?, 'department': ?}}"

        try:
            self.dynamodb.execute_transaction(
                TransactStatements=[
                    {
                        "Statement": statement,
                        "Parameters": [
                            {"S": "USERS"},
                            {"S": ("EMAIL#" + new_user.email + "#UUID#" + new_user.id)},
                            {"S": new_user.id},
                            {"S": new_user.email},
                            {"S": new_user.name},
                            {"S": new_user.mobile},
                            {"S": new_user.password},
                            {"S": new_user.role.value},
                            {"S": str(new_user.department.value) if new_user.department else ""},
                        ],
                    },
                    {
                        "Statement": statement,
                        "Parameters": [
                            {"S": ("ROLE#" + new_user.role.value.upper())},
                            {"S": f"DEPARTMENT#{str(new_user.department.value)}#UUID#{new_user.id}" if new_user.department else f"UUID#{new_user.id}"},
                            {"S": new_user.id},
                            {"S": new_user.email},
                            {"S": new_user.name},
                            {"S": new_user.mobile},
                            {"S": new_user.password},
                            {"S": new_user.role.value},
                            {"S": str(new_user.department.value) if new_user.department else ""},
                        ],
                    },
                ],
            )
        except Exception:
            raise AppException(USER_006)
        

    def get_all_users_by_role(self, role: UserRole, department: Department | None) -> List[User]:
        try:
            if department is None:
                response = self.dynamodb.execute_statement(
                Statement=f"""
                    SELECT * FROM {self.table_name}
                    WHERE PK = ?
                """,
                Parameters=[
                    {"S": f"ROLE#{role.value.upper()}"}
                ]
            )
            else:
                response = self.dynamodb.execute_statement(
                    Statement=f"""
                        SELECT * FROM {self.table_name}
                        WHERE PK = ?
                        AND begins_with(SK, ?)
                    """,
                    Parameters=[
                        {"S": f"ROLE#{role.value.upper()}"},
                        {"S": f"DEPARTMENT#{department.value}"}
                    ]
                )
        except:
            raise AppException(USER_007)

        items = response["Items"]

        users: List[User] = []

        for item in items:
            user_details = {k: self.deserializer.deserialize(v) for k, v in item.items()}
            
            user: User = User.model_construct(**user_details)

            users.append(user) 

        return users  


        
