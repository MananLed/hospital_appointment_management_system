from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from app.response.response import Response
from app.controller.auth_controller import auth_router


app = FastAPI()
app.include_router(auth_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error_response(
            error_code="SYS_001",
            message=exc.detail,
        ),
    )
