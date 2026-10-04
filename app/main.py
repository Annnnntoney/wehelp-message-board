from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.errors import AppError, app_error_handler
from app.messages import router as messages_router

app = FastAPI(title="message-board")
app.add_exception_handler(AppError, app_error_handler)
app.include_router(messages_router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """給 Docker、CD smoke test、之後的 Load Balancer 用的健康檢查。"""
    return {"status": "ok"}


# 放最後：上面的 API 都沒對到，才去 static/ 找檔案；html=True 讓 / 回傳 index.html
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
