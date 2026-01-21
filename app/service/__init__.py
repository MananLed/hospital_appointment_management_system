from app.repository import auth_repository_instance
from app.service.auth_service import AuthService


auth_service_instance = AuthService(auth_repository_instance)