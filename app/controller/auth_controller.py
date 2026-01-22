from fastapi import APIRouter, status
from app.service import user_service_instance
from app.dto.user import LoginInput, SignUpInput
from app.models.user import User
from app.response.response import Response


auth_router = APIRouter(prefix="/auth")

@auth_router.post("/login")
def login(login_details: LoginInput):

    access_data = user_service_instance.get_user_by_email_and_password(login_details.email, login_details.password)

    return Response.success_response(access_data, "Login Successful", status.HTTP_201_CREATED)


@auth_router.post("/signup")
def signup(signup_details: SignUpInput):

    signup_details.email = signup_details.email.lower()
    signup_details.department = ""
    
    new_user: User = User.model_construct(**signup_details.model_dump())

    user_service_instance.add_user(new_user)

    return Response.success_response(None, "Sign Up Successful", status.HTTP_201_CREATED)