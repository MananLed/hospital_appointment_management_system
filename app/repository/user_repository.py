from app.models.user import User
from app.constants.constants import * 
from app.errors.base_exception import AppException


class UserRepository:
    def __init__(self, ddb_connection, deserializer, table_name):
        self.deserializer = deserializer()
        self.dynamodb = ddb_connection
        self.table_name = table_name    

    def get_user_by_email(self, email: str):
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
            
            
    def add_user(self, new_user: User):
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
                            {"S": new_user.department or ""},
                        ],
                    },
                    {
                        "Statement": statement,
                        "Parameters": [
                            {"S": ("ROLE#" + new_user.role.value.upper())},
                            {"S": ("UUID#" + new_user.id)},
                            {"S": new_user.id},
                            {"S": new_user.email},
                            {"S": new_user.name},
                            {"S": new_user.mobile},
                            {"S": new_user.password},
                            {"S": new_user.role.value},
                            {"S": new_user.department or ""},
                        ],
                    },
                ],
            )
        except Exception:
            raise AppException(USER_006)


        
