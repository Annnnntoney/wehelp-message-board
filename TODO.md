# 後端待辦：message-board

**照著做：[docs/TUTORIAL.md](./docs/TUTORIAL.md)**（零基礎完整教學）。規格見 [docs/SPEC.md](./docs/SPEC.md)，API 見 [docs/API-CONTRACT.md](./docs/API-CONTRACT.md)，CI/CD 見 [docs/CICD.md](./docs/CICD.md)。

> 簡報沒寫第一週的繳交期限。先抓 **10/9（五）交**，留週末準備 10/12 的個人專案期初報告；確認期限後再調。
> AWS 設定（網域生效、RDS 建立）要等，所以排在前面跟寫程式並行。

## 10/4（日）專案初始化

- [x] FastAPI 骨架：`app/main.py`、`/healthz`、pytest
- [x] Ruff、`pyproject.toml`、`requirements*.txt`
- [x] Dockerfile（python:3.12-slim、非 root）、`.dockerignore`、`.env.example`
- [x] CI：`ci.yml`（ruff、pytest、docker build + smoke、gitleaks）
- [x] CD：`deploy.yml`（Docker Hub → EC2，`DEPLOY_ENABLED` 開關）
- [x] README、API 契約、CI/CD 計劃、PR template
- [x] `git init` + 第一個 commit
- [ ] GitHub 建 repo，push `main`，確認 CI 綠燈
- [x] **買網域**：Cloudflare `antoney.com`，留言板用 `board.antoney.com`
- [ ] AWS：開 Billing alarm（例如 US$5），確認用的是 Free Tier 規格

## 10/5（一）AWS 資源

- [ ] S3 bucket：Block all public access
- [ ] CloudFront distribution：Origin = 該 bucket，用 OAC；記下 `dxxxx.cloudfront.net`
- [ ] RDS MySQL（Free Tier、不開 Public access），Security Group 只允許 EC2 的 SG
- [ ] EC2（Amazon Linux 2023、t3.micro）、Elastic IP、IAM Role（`s3:PutObject`／`s3:DeleteObject`）、metadata hop limit = 2
- [ ] EC2 裝 Docker，建 `~/message-board/.env`
- [ ] 網域 A 紀錄 → Elastic IP

## 10/6（二）API

- [ ] `app/config.py`：讀 `.env`
- [ ] `schema.sql`，從 EC2 連 RDS 建表
- [ ] `app/storage.py`：boto3 上傳 S3、組 CloudFront 網址
- [ ] `app/database.py`：新增、列出（新到舊）
- [ ] `POST /api/messages`、`GET /api/messages`，錯誤格式照 API 契約
- [ ] 把 `boto3`、`python-multipart`、DB driver 加進 `requirements.txt`；`moto` 加進 dev

## 10/7（三）頁面與測試

- [ ] `app/static/index.html`：「發表一篇圖文」表單 + 列表，送出後新留言在最上面
- [ ] 測試：驗證規則、`POST` 成功／4xx、`GET` 排序、DB 失敗時刪 S3 物件（moto + SQLite）
- [ ] 本機 `docker build` + `docker run --env-file .env` 跑通（連真 AWS）

## 10/8（四）部署

- [ ] 先手動部署一次：本機 build `linux/amd64` → push Docker Hub → EC2 pull／run
- [ ] 線上確認：發文、圖片網址是 CloudFront、重新整理後還在
- [ ] GitHub 設 Secrets／Variables（CICD.md §3.1），最後設 `DEPLOY_ENABLED=true`
- [ ] 開一個小 PR 走完整條 CI/CD，跑 CICD.md §7 的驗收
- [ ] `main` 開 branch protection

## 10/9（五）繳交

- [ ] README 補線上網址、截圖
- [ ] 私訊講師：網域網址 + GitHub repo 連結
- [ ] repo 若是 private，記得把講師加成 collaborator

## 本週驗收

- 用自己的網域打得開留言板
- 留言 + 附圖成功，列表新到舊，圖片從 CloudFront 載入
- 資料在 RDS、圖片在 S3；程式和 repo 裡沒有任何 key
- 用 Docker 跑在 EC2；merge 進 `main` 會自動部署
