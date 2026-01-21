from app.repository.auth_repository import AuthRepository
from app.dto.user import SignUpInput

class AuthService:
    def __init__(self, auth_repository_instance: AuthRepository):
        self.auth_repository = auth_repository_instance

    def get_access_token(self, email: str, password: str):

        tokens = self.auth_repository.get_access_token(email, password)

        return {"tokens": tokens}
    
    def add_user(self, signup_details: SignUpInput): #Add role 

        self.auth_repository.add_user(signup_details)