from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """可以直接回給使用者的錯誤：HTTP status + 錯誤代碼 + 中文訊息。"""

    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )
