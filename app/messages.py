import logging
from datetime import datetime
from typing import Annotated, Any

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy import Engine

from app import database, storage
from app.config import get_settings
from app.errors import AppError

router = APIRouter(prefix="/api/messages", tags=["messages"])
logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 1000

# 依賴注入：路由不自己建連線，由 FastAPI 傳進來；測試時可以換成假的
EngineDep = Annotated[Engine, Depends(database.get_engine)]
S3Dep = Annotated[Any, Depends(storage.get_s3_client)]


class Message(BaseModel):
    id: int
    content: str
    imageUrl: str
    createdAt: datetime


class MessageResponse(BaseModel):
    data: Message


class MessageListResponse(BaseModel):
    data: list[Message]


def to_message(row: dict) -> Message:
    return Message(
        id=row["id"],
        content=row["content"],
        imageUrl=storage.image_url(row["image_key"]),
        createdAt=row["created_at"],
    )


# 用 def 而不是 async def：boto3 和 PyMySQL 都是同步（會卡住）的套件，
# FastAPI 會把 def 的路由丟到 thread pool 執行，不會擋住其他請求。
@router.get("", response_model=MessageListResponse)
def list_messages(engine: EngineDep):
    rows = database.list_messages(engine)
    return {"data": [to_message(row) for row in rows]}


@router.post("", status_code=201, response_model=MessageResponse)
def create_message(
    engine: EngineDep,
    s3: S3Dep,
    content: Annotated[str, Form()] = "",
    image: Annotated[UploadFile | None, File()] = None,
):
    content = content.strip()
    if not content or len(content) > MAX_CONTENT_LENGTH:
        raise AppError(400, "invalid_content", f"文字內容請輸入 1 到 {MAX_CONTENT_LENGTH} 字")
    if image is None or not image.filename:
        raise AppError(400, "image_required", "請選擇一張圖片")

    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    data = image.file.read(max_bytes + 1)  # 多讀 1 byte 就知道有沒有超過
    if len(data) > max_bytes:
        raise AppError(413, "image_too_large", f"圖片不能超過 {get_settings().max_upload_mb}MB")

    image_type = storage.detect_image_type(data)
    if image_type is None:
        raise AppError(415, "unsupported_image", "只接受 JPG、PNG、GIF、WebP 圖片")
    extension, content_type = image_type

    try:
        key = storage.upload_image(s3, data, extension, content_type)
    except (BotoCoreError, ClientError):
        logger.exception("S3 upload failed")
        raise AppError(502, "upload_failed", "圖片上傳失敗，請稍後再試") from None

    try:
        row = database.insert_message(engine, content, key)
    except Exception:
        # 資料庫寫失敗，就把剛上傳的圖刪掉，S3 才不會留下沒人用的檔案
        logger.exception("DB insert failed")
        try:
            storage.delete_image(s3, key)
        except (BotoCoreError, ClientError):
            logger.exception("Failed to clean up %s", key)
        raise AppError(500, "internal_error", "留言儲存失敗，請稍後再試") from None

    return {"data": to_message(row)}
