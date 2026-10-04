from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # pool_pre_ping：RDS 會切掉閒置太久的連線，用之前先確認還活著
    return create_engine(get_settings().sqlalchemy_url, pool_pre_ping=True, pool_recycle=3600)


def insert_message(engine: Engine, content: str, image_key: str) -> dict:
    with engine.begin() as conn:
        result = conn.execute(
            text("INSERT INTO messages (content, image_key) VALUES (:content, :image_key)"),
            {"content": content, "image_key": image_key},
        )
        row = conn.execute(
            text("SELECT id, content, image_key, created_at FROM messages WHERE id = :id"),
            {"id": result.lastrowid},
        ).one()
    return _to_dict(row)


def list_messages(engine: Engine) -> list[dict]:
    with engine.connect() as conn:
        rows = conn.execute(
            # 用 id 排序：同一秒送出的兩則，created_at 會一樣，id 不會
            text("SELECT id, content, image_key, created_at FROM messages ORDER BY id DESC")
        ).all()
    return [_to_dict(row) for row in rows]


def _to_dict(row) -> dict:
    created_at = row.created_at
    if isinstance(created_at, str):  # SQLite 回傳字串，MySQL 回傳 datetime
        created_at = datetime.fromisoformat(created_at)
    return {
        "id": row.id,
        "content": row.content,
        "image_key": row.image_key,
        # RDS 預設時區是 UTC，補上時區資訊讓前端能正確換算
        "created_at": created_at.replace(tzinfo=timezone.utc),
    }
