from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """從環境變數（或 .env）讀設定，名稱不分大小寫。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "admin"
    db_password: str = ""
    db_name: str = "message_board"
    # 有填就直接用（測試用 SQLite）；沒填就用上面五個欄位組 MySQL 連線
    database_url: str | None = None

    aws_region: str = "ap-northeast-1"
    s3_bucket: str = ""
    # 以下三個只有本機用 moto 模擬 S3 時才填；線上留空，boto3 會自動用 EC2 的 IAM Role
    s3_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    # 圖片網址前綴，線上填 https://dxxxx.cloudfront.net
    cdn_base_url: str = ""

    max_upload_mb: int = 5

    @property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        # 用 URL.create 組，密碼裡有 @、# 等特殊字元也不會壞
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
