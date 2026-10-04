import uuid
from functools import lru_cache

import boto3

from app.config import get_settings

# 檔案開頭的固定位元組（magic number），比瀏覽器送來的 Content-Type 可靠
_SIGNATURES = {
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"GIF87a": ("gif", "image/gif"),
    b"GIF89a": ("gif", "image/gif"),
}


def detect_image_type(data: bytes) -> tuple[str, str] | None:
    """回傳 (副檔名, MIME type)；不是支援的圖片格式回傳 None。"""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    for signature, image_type in _SIGNATURES.items():
        if data.startswith(signature):
            return image_type
    return None


@lru_cache
def get_s3_client():
    settings = get_settings()
    # 金鑰是 None 時 boto3 會自己找憑證；在 EC2 上就是掛在機器上的 IAM Role
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def upload_image(s3, data: bytes, extension: str, content_type: str) -> str:
    key = f"uploads/{uuid.uuid4().hex}.{extension}"
    s3.put_object(
        Bucket=get_settings().s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
        # 檔名不會重複，可以讓瀏覽器和 CloudFront 快取一年
        CacheControl="public, max-age=31536000, immutable",
    )
    return key


def delete_image(s3, key: str) -> None:
    s3.delete_object(Bucket=get_settings().s3_bucket, Key=key)


def image_url(key: str) -> str:
    return f"{get_settings().cdn_base_url.rstrip('/')}/{key}"
