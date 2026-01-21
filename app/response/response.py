from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any

class Response:

    @classmethod
    def success_response(cls, data: Any, message: str, status_code: int):

        return JSONResponse(
            status_code=status_code,
            content={"status": "Success", "message": message, "data": jsonable_encoder(data, by_alias=True)},
        )

    @classmethod
    def error_response(cls, error_code: str, message: str):
        return {
            "status": "fail",
            "errorcode": error_code,
            "message": message,
        }