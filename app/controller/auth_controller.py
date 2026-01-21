from fastapi import APIRouter, status
from app.service import auth_service_instance
from app.dto.user import LoginInput, SignUpInput
from app.response.response import Response


auth_router = APIRouter(prefix="/auth")

@auth_router.post("/login")
def login(login_details: LoginInput):

    tokens = auth_service_instance.get_access_token(login_details.email, login_details.password)

    return Response.success_response(tokens, "Login Successful", status.HTTP_201_CREATED)


@auth_router.post("/signup")
def signup(signup_details: SignUpInput):
    
    auth_service_instance.add_user(signup_details)

    return Response.success_response(None, "Sign Up Successful", status.HTTP_201_CREATED)