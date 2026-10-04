# message-board

WeHelp 最後階段第一週後端任務：圖文留言板（AWS S3 + CloudFront + RDS，用 Docker 部署到 EC2）。

## 網站

| 環境   | 連結                           |
| ------ | ------------------------------ |
| 線上   | （網域設好後填入）             |
| 本機   | http://localhost:8000          |
| 原始碼 | https://github.com/Annnnntoney/wehelp-message-board |

## 技術

| 項目     | 選擇                                       |
| -------- | ------------------------------------------ |
| 語言     | Python 3.12（Docker／CI）；本機 ≥ 3.10 可跑 |
| 框架     | FastAPI + Uvicorn                          |
| 資料庫   | AWS RDS for MySQL                          |
| 圖片     | AWS S3（boto3）+ CloudFront CDN            |
| 部署     | Docker image → Docker Hub → EC2            |
| 網域     | GoDaddy 或 Cloudflare，A 紀錄指向 EC2      |

## 架構

```
上傳：使用者 ──▶ Web App（EC2 / Docker）──▶ S3（圖片）
                                       └──▶ RDS（文字 + image_key）

讀取：使用者 ◀── Web App ◀── RDS
      使用者 ◀── CloudFront ◀── S3（圖片不經過 Web App）
```

## 檔案規劃

| 路徑                 | 內容                                    |
| -------------------- | --------------------------------------- |
| `app/main.py`        | FastAPI app、路由註冊、`/healthz`       |
| `app/config.py`      | 讀環境變數                              |
| `app/errors.py`      | 統一錯誤格式                            |
| `app/database.py`    | RDS 連線、`messages` 表存取             |
| `app/storage.py`     | 上傳 S3、組 CloudFront 網址             |
| `app/messages.py`    | `GET`／`POST /api/messages`             |
| `app/static/`        | 留言板頁面（表單 + 列表）               |
| `scripts/dev_setup.py` | 本機模擬模式初始化（SQLite + 假 S3）  |
| `schema.sql`         | 建表 SQL                                |
| `tests/`             | pytest（S3 用 moto mock、DB 用 SQLite） |

目前只有 `app/main.py` 的 `/healthz`，其餘照 [docs/TUTORIAL.md](./docs/TUTORIAL.md) 和 [TODO.md](./TODO.md) 補。

## 本機

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.local.example .env  # 本機模擬模式，不需要 AWS；細節見 docs/TUTORIAL.md §4.13
uvicorn app.main:app --reload
```

| 指令                  | 用途            |
| --------------------- | --------------- |
| `ruff check .`        | Lint            |
| `ruff format .`       | 格式化          |
| `pytest`              | 測試            |
| `docker build -t message-board .` | 建 image |
| `docker run -p 8000:8000 --env-file .env message-board` | 本機跑 container |

## AI Code Review

PR 由 [Sourcery](https://sourcery.ai)（GitHub App，public repo 免費）自動審查，設定在 [.sourcery.yaml](./.sourcery.yaml)。

| 在 PR 留言            | 作用                     |
| --------------------- | ------------------------ |
| `@sourcery-ai review` | 重新審查                 |
| `@sourcery-ai summary`| 產生 PR 摘要             |
| `@sourcery-ai guide`  | 產生審查者指南           |
| `@sourcery-ai resolve`| 標記所有 Sourcery 評論已處理 |

不想被審查的 PR 加上 `sourcery-ignore` label。

## 文件

- **零基礎教學（從頭到尾）**：[docs/TUTORIAL.md](./docs/TUTORIAL.md)
- 任務規格：[docs/SPEC.md](./docs/SPEC.md)
- API 契約：[docs/API-CONTRACT.md](./docs/API-CONTRACT.md)
- CI/CD 計劃：[docs/CICD.md](./docs/CICD.md)
- 待辦與排程：[TODO.md](./TODO.md)

## 繳交

Docker 部署上線後私訊講師：**上線網址（自己的網域）** + **GitHub Repository 連結**。
