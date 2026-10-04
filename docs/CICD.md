# CI/CD 計劃：message-board（後端）

CI 用 GitHub Actions；CD 照簡報「Docker 部署流程 - 1」：build image → push 到 Docker Hub → EC2 pull → run，全部交給 Actions 自動做。

```
feat/* ──PR──▶ CI（lint／test／docker build＋smoke／gitleaks）
                 │ 全綠
                 ▼
            merge 進 main ──▶ CI 再跑一次 ──綠──▶ Deploy workflow
                                                  ├─ build linux/amd64 image
                                                  ├─ push Docker Hub（:<sha>、:latest）
                                                  ├─ SSH 進 EC2：pull → 換 container
                                                  └─ curl 線上 /healthz
```

## 1. 分支策略

| 分支     | 用途                             | 部署       |
| -------- | -------------------------------- | ---------- |
| `main`   | 隨時可上線；只能透過 PR 合併     | 自動部署 EC2 |
| `feat/*` | 一個功能一條                     | 不部署，只跑 CI |
| `fix/*`  | 修 bug                           | 不部署，只跑 CI |

Squash merge，合併後刪分支。

## 2. CI：`.github/workflows/ci.yml`

觸發：push 到 `main`、任何 PR。

| Job       | 步驟                                                 | 擋下什麼                           |
| --------- | ---------------------------------------------------- | ---------------------------------- |
| `quality` | `ruff check` → `ruff format --check` → `pytest`      | 語法、import、格式、邏輯回歸       |
| `docker`  | `docker build` → 跑 container → 打 `/healthz`        | Dockerfile 壞掉、app 起不來        |
| `secrets` | gitleaks 掃全部歷史                                  | commit 進去的 AWS key、DB 密碼     |

### 測試策略

| 層級     | 工具                          | 測什麼                                           |
| -------- | ----------------------------- | ------------------------------------------------ |
| 單元     | pytest                        | 驗證規則（空白、超長、檔案大小、MIME）、CloudFront 網址組法 |
| API      | `TestClient` + moto + SQLite  | `POST` 成功／各種 4xx、`GET` 排序新到舊、DB 失敗時刪 S3 物件 |
| 整合（第二階段） | CI 加 `services: mysql:8` | 真的 MySQL 跑 `schema.sql` 與查詢，抓 SQLite 和 MySQL 的差異 |

CI 永遠不碰真的 AWS：S3 用 moto mock，不需要在 GitHub 放 AWS key。

## 3. CD：Docker Hub → EC2

### 3.1 一次性設定

**Docker Hub**

1. 建 repo `wehelp-message-board`（public 即可，image 裡沒有機密）。
2. Account Settings → Personal access tokens → 建一個 Read & Write token。

**EC2**

1. 裝 Docker，把登入使用者加進 `docker` 群組。
2. 建 `~/message-board/.env`，內容照 `.env.example` 填真實值，`chmod 600`。**這份只存在 EC2，不進 GitHub。**
3. EC2 掛 IAM Role（只給該 bucket 的 `s3:PutObject`、`s3:DeleteObject`），程式不放 AWS key。
4. Container 裡的 boto3 要經 IMDSv2 拿 Role 憑證：EC2 → Modify instance metadata options → **hop limit 設 2**，否則 container 拿不到憑證。
5. Security Group：80 對外開；22 只開給自己的 IP 和 GitHub Actions（見 §5 的風險）。

**GitHub repo → Settings**

| 位置                   | 名稱                  | 值                               |
| ---------------------- | --------------------- | -------------------------------- |
| Secrets → Actions      | `DOCKERHUB_TOKEN`     | Docker Hub token                 |
| Secrets → Actions      | `EC2_HOST`            | EC2 公開 IP（Elastic IP）        |
| Secrets → Actions      | `EC2_USER`            | `ec2-user`（AL2023）或 `ubuntu`  |
| Secrets → Actions      | `EC2_SSH_KEY`         | 部署專用 private key 全文        |
| Variables → Actions    | `DOCKERHUB_USERNAME`  | Docker Hub 帳號                  |
| Variables → Actions    | `APP_URL`             | `http://你的網域`                |
| Variables → Actions    | `DEPLOY_ENABLED`      | `true`（設好上面全部之後才設）   |
| Environments           | `production`          | （選）加 required reviewer 當手動閘門 |

`DEPLOY_ENABLED` 沒設時 deploy workflow 會直接跳過，所以 AWS 還沒準備好也可以先 push。

### 3.2 `.github/workflows/deploy.yml` 做什麼

1. 觸發：CI 在 `main` 跑完且成功（`workflow_run`），或手動 **Run workflow**。
2. `image` job：buildx 建 **linux/amd64** image（避免 Apple Silicon 建出 arm64 在 EC2 跑不動），push `:<commit sha>` 和 `:latest`。
3. `deploy` job：SSH 進 EC2 → `docker pull :<sha>` → 刪舊 container → `docker run --restart always -p 80:8000 --env-file ~/message-board/.env` → 清舊 image。
4. Smoke test：打 `APP_URL/healthz`，60 秒內沒回應就標紅。
5. `concurrency: deploy-production`：兩次部署不會同時跑。

部署用 **commit sha** 當 tag，不用 `latest`，線上跑的是哪個版本一看就知道，回滾也有依據。

### 回滾

在 Actions 找上一個成功的 Deploy run，用它的 sha：

```bash
# EC2 上
docker rm -f message-board
docker run -d --name message-board --restart always \
  -p 80:8000 --env-file ~/message-board/.env \
  <帳號>/wehelp-message-board:<上一個 sha>
```

或在 GitHub revert 那個 PR，讓 CI/CD 自動重新部署。

### 資料庫 schema

第一週手動執行：從 EC2 用 `mysql` client 連 RDS 跑一次 `schema.sql`（`CREATE TABLE IF NOT EXISTS`，重跑無害）。之後 schema 開始改，再引入 Alembic，並在 deploy 前加一步 migration。

## 4. 簡報流程 2 的替代做法

「Docker 部署流程 - 2」是 EC2 `git pull` 後在機器上 build。要改用這種，把 deploy job 的 script 換成：

```bash
cd ~/message-board/src && git pull
docker build -t message-board .
docker rm -f message-board 2>/dev/null || true
docker run -d --name message-board --restart always -p 80:8000 --env-file ~/message-board/.env message-board
```

不需要 Docker Hub，但 EC2 要能讀 repo（private 要 deploy key），小規格機器 build 會慢。預設用流程 1。

## 5. 風險與之後的升級

| 現況                         | 風險                                  | 升級方向                                       |
| ---------------------------- | ------------------------------------- | ---------------------------------------------- |
| SSH 部署，22 port 要讓 Actions 連 | GitHub runner IP 範圍很大，等於半開放 | 改 AWS SSM Run Command + GitHub OIDC 角色，22 port 全關、不存 SSH key |
| `.env` 手放在 EC2            | 換機器要手動搬                        | AWS Secrets Manager／SSM Parameter Store       |
| HTTP 80                      | 明碼傳輸                              | 第二週：Nginx + HTTPS、Load Balancer           |
| 單台 EC2、換 container 有幾秒中斷 | 部署瞬間 502                       | 第二週 Load Balancer 後面放兩台輪流換          |

## 6. Branch protection（`main`）

- [ ] Require a pull request before merging
- [ ] Require status checks：`Lint / Format / Test`、`Docker build + smoke`、`Secret scan`
- [ ] Do not allow force pushes

## 7. 驗收

- [ ] PR 上 CI 三個 job 全綠
- [ ] 故意讓一個測試失敗，確認 CI 變紅、不能 merge，**也不會部署**
- [ ] merge 後 Deploy 自動跑完，Docker Hub 出現該 sha 的 tag
- [ ] 線上 `/healthz` 回 `{"status":"ok"}`，留言板能發文、圖片從 CloudFront 網址載入
- [ ] 照「回滾」步驟退回上一版再升回來
