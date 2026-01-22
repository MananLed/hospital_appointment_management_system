from app.repository import user_repository_instance
from app.service.user_service import UserService


user_service_instance = UserService(user_repository_instance)