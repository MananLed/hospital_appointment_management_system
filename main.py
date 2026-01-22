from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from app.constants.constants import *
from fastapi.responses import JSONResponse
from app.response.response import Response
from app.errors.base_exception import AppException

from app.controller.auth_controller import auth_router


app = FastAPI()
app.include_router(auth_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.exception_handler(AppException)
def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error_response(
            error_code=exc.error_code,
            message=exc.detail,
        ),
    )

@app.exception_handler(RequestValidationError)
def app_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=Response.error_response(
            error_code=SYS_001,
            message=INVALID_DETAILS,
        ),
    )

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error_response(
            error_code=SYS_001,
            message=exc.detail,
        ),
    )

@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=Response.error_response(
            error_code=SYS_001,
            message=SERVER_ERROR,
        ),
    )
