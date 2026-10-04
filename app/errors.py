import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """可以直接回給使用者的錯誤：HTTP status + 錯誤代碼 + 中文訊息。"""

    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message


def error_response(status_code: int, error: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": error, "message": message})


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.error, exc.message)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI 預設回 422 + detail，統一改成跟其他錯誤一樣的格式
    return error_response(400, "invalid_request", "送出的資料格式不正確")


async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    # 沒預料到的錯誤（例如資料庫掛了）：細節只寫進 log，使用者只看到通用訊息
    logger.exception("Unhandled error", exc_info=exc)
    return error_response(500, "internal_error", "伺服器發生錯誤，請稍後再試")
