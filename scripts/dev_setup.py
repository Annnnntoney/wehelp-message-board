"""本機模擬模式：建 SQLite 資料表 + 在 moto 假 S3 上建 bucket。

先開另一個終端機跑 `moto_server -p 5001`，再執行：
    python scripts/dev_setup.py
"""

import json
import sqlite3

import boto3

DB_FILE = "local.db"
BUCKET = "local-bucket"
MOTO_URL = "http://localhost:5001"

with sqlite3.connect(DB_FILE) as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          content VARCHAR(1000) NOT NULL,
          image_key VARCHAR(255) NOT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
print(f"SQLite ready: {DB_FILE}")

s3 = boto3.client(
    "s3",
    region_name="us-east-1",
    endpoint_url=MOTO_URL,
    aws_access_key_id="local",
    aws_secret_access_key="local",
)
s3.create_bucket(Bucket=BUCKET)
# 只有本機假 S3 才開放公開讀取；真的 S3 要保持 Block Public Access，交給 CloudFront 讀
s3.put_bucket_policy(
    Bucket=BUCKET,
    Policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{BUCKET}/*",
                }
            ],
        }
    ),
)
print(f"Fake S3 bucket ready: {MOTO_URL}/{BUCKET}")
