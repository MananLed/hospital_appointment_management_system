from app.repository.user_repository import UserRepository
from app.models.user import User, UserRole, Department
from app.dto.user import AuthResponse
from app.errors.base_exception import AppException
from app.constants.constants import *
from app.utils.hash_and_check_password import compare_hash_and_password, generate_hash_from_password
from app.utils.jwt import create_jwt_token
from typing import List

class UserService:
    def __init__(self, user_repository_instance: UserRepository):
        self.user_repository = user_repository_instance

    def get_user_by_email_and_password(self, email: str, password: str) -> AuthResponse:

        user: User = self.user_repository.get_user_by_email(email)

        if not compare_hash_and_password(password, user.password):
            raise AppException(USER_001)

        access_token = create_jwt_token(user.id, user.role, user.email)

        return {"token": access_token, "email": user.email, "role": user.role}
    
    def add_user(self, user: User, role: UserRole | None = None) -> None:

        if role is not None:
            user.role = role

        try:
            existing_user: User = self.user_repository.get_user_by_email(user.email)
        except AppException as exception:
            if exception.error_code == USER_005:
                existing_user = None
            else:
                raise exception

        if existing_user is not None:
            raise AppException(USER_002)

        try:
            user.password = generate_hash_from_password(user.password)
        except:
            raise AppException(USER_003)

        self.user_repository.add_user(user)

    
    def get_all_users_by_role(self, role: UserRole, department: Department | None = None, id: str | None = None) -> List[User]:
        return self.user_repository.get_all_users_by_role(role, department, id)