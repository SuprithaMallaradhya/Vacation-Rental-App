from typing import Literal

from pydantic import BaseModel, ConfigDict


class Success[Data](BaseModel):
    success: Literal[True] = True
    data: Data


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "UNAUTHENTICATED",
                        "message": "A valid bearer token is required",
                        "details": [],
                    },
                    "request_id": "22222222-2222-4222-8222-222222222222",
                }
            ]
        }
    )
    success: Literal[False] = False
    error: ErrorBody
    request_id: str
