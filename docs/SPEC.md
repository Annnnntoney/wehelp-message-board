# WeHelp 最後階段：後端第一週任務

> 來源：`第一週深入主題說明.pptx`（Slides 1、9–18、20–29）
> 標註「📌 簡報原文」的是投影片內容；標註「💡 補充」的是依簡報推導出的實作建議，不是講師要求。

---

## 1. 後端深入主題：AWS 雲端架構的運用

| 週次 | 主題 |
|---|---|
| **第一週（本週）** | 決定語言和框架、Domain Name、AWS S3、CloudFront、RDS、Deployed by Docker |
| 第二週 | Nginx、HTTPS、AWS Load Balancer |

---

## 2. 工作描述：完成 AWS 雲端服務整合練習專案

📌 簡報原文：

1. 在 **GoDaddy** 或 **Cloudflare** 購買網域，設定 **DNS 紀錄**。
2. 建立一個**圖文留言板**：使用者可以留言並附圖，頁面顯示留言列表。
3. 用 **AWS S3** 存圖片，用 **AWS CloudFront** 建立 CDN，用 **AWS RDS** 建立資料庫。
4. 用 **Docker** 部署上線後，私訊講師：**上線網址** + **GitHub Repository 原始碼**。

### 繳交清單

- [ ] 上線網址（使用自己的網域）
- [ ] GitHub Repository 連結

---

## 3. 畫面規格（依簡報截圖 Slides 12–13）

頁面刻意保持陽春，重點在後端架構。

```
發表一篇圖文
文字內容 [______________]
圖片檔案 [Choose File] No file chosen
[送出]
────────────────────────────────
測試看看這個
[圖片]
────────────────────────────────
看看
[圖片]
────────────────────────────────
```

| 區塊 | 內容 |
|---|---|
| 標題 | 「**發表一篇圖文**」 |
| 文字內容 | 文字輸入框 |
| 圖片檔案 | `<input type="file">` |
| 送出 | 按鈕「**送出**」 |
| 留言列表 | 每則留言 = 文字 + 圖片，以 `<hr>` 分隔 |

**行為（兩張截圖對照）**：送出前文字框填「選擇一張圖片後送出」並選好圖片；送出後這則留言出現在**列表最上方**，代表列表依時間**新到舊**排序。

### 功能需求

- [ ] 輸入文字、選擇圖片後送出，建立一則留言
- [ ] 圖片上傳到 S3
- [ ] 文字與圖片網址存進 RDS
- [ ] 頁面載入時從 RDS 讀出所有留言，新的在最上面
- [ ] 圖片透過 CloudFront 網址顯示，不直接用 S3 網址

---

## 4. 系統架構與資料流

### 4.1 上傳圖文內容（Slide 14）

📌 簡報原文：

```
                 EC2 Instance
              ┌──────────────────┐
              │ Docker Container │
 使用者 ─────▶│     Web App      │─────▶ RDS
              └────────┬─────────┘
                       ▼
       CloudFront ◀─── S3
```

1. 使用者把文字 + 圖片送到 Web App（EC2 上的 Docker Container）。
2. Web App 把**圖片上傳到 S3**。
3. Web App 把**文字與圖片資訊寫入 RDS**。
4. S3 是 CloudFront 的來源（Origin）。

### 4.2 取得圖文內容（Slide 15）

📌 簡報原文：

```
                 EC2 Instance
              ┌──────────────────┐
              │ Docker Container │
 使用者 ◀─────│     Web App      │◀───── RDS
   ▲          └──────────────────┘
   │
   └──────── CloudFront ◀─── S3
```

1. Web App **從 RDS 讀出留言**，回傳給使用者。
2. 使用者的瀏覽器**透過 CloudFront 載入圖片**，CloudFront 再向 S3 取檔並快取。
3. 圖片流量不經過 Web App。

---

## 5. 💡 補充：實作建議

簡報只要求「決定語言和框架」；本專案已選定 **Python + FastAPI**。API 與資料表以 [API-CONTRACT.md](./API-CONTRACT.md) 為準，Dockerfile 以 repo 根目錄的 `Dockerfile` 為準，本節保留作背景說明。

### 5.1 技術選型範例

| 項目 | 範例 |
|---|---|
| 語言 / 框架 | Python + FastAPI / Flask，或 Node.js + Express |
| 資料庫 | AWS RDS for MySQL 或 PostgreSQL |
| S3 SDK | Python `boto3` / Node `@aws-sdk/client-s3` |
| 部署 | Docker（EC2 上執行） |

### 5.2 資料表

```sql
CREATE TABLE messages (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  content     VARCHAR(1000) NOT NULL,
  image_key   VARCHAR(255)  NOT NULL,     -- S3 object key，例如 uploads/<uuid>.jpg
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

建議存 **S3 object key**，回傳時再拼成 `https://<CloudFront 網域>/<image_key>`，之後換 CDN 網域不必改資料。

### 5.3 API

| Method | Path | 說明 |
|---|---|---|
| `GET` | `/` | 留言板頁面 |
| `POST` | `/api/messages` | `multipart/form-data`（`content`、`image`）；上傳圖片到 S3 → 寫入 RDS |
| `GET` | `/api/messages` | 依 `created_at DESC` 回傳列表，每筆含 CloudFront 圖片網址 |

`GET /api/messages` 回應範例：

```json
{
  "data": [
    { "id": 3, "content": "測試看看這個", "imageUrl": "https://dxxxx.cloudfront.net/uploads/abc.jpg", "createdAt": "2026-10-04T12:00:00Z" }
  ]
}
```

### 5.4 AWS 設定重點

**S3**
- 開一個 bucket，維持 **Block all public access**。
- 檔名用 UUID，避免撞名與猜測。

**CloudFront**
- Origin 指向該 S3 bucket，用 **Origin Access Control (OAC)**，讓 bucket 只開放給 CloudFront 讀取。
- 拿到 `dxxxx.cloudfront.net` 網域，當作圖片網址前綴。

**RDS**
- Security Group 只允許 EC2 的 Security Group 連 3306 / 5432，不要開放 `0.0.0.0/0`。

**EC2**
- 給 EC2 一個 **IAM Role**，權限只開 `s3:PutObject`（限該 bucket），就不必在程式裡放 Access Key。
- Security Group 開 80（第二週再處理 443 / HTTPS）。

**機密設定**
- RDS 帳密、bucket 名稱、CloudFront 網域放在環境變數或 `.env`，不要 commit 進 Git。

### 5.5 輸入驗證（建議）

- 文字與圖片皆必填。
- 只接受圖片 MIME type（`image/jpeg`、`image/png`、`image/webp` 等）。
- 限制檔案大小（例如 5MB）。

---

## 6. 網域與 DNS

1. 在 GoDaddy 或 Cloudflare 購買網域。
2. 新增 **A 紀錄**指向 EC2 的公開 IP。💡 建議幫 EC2 綁 **Elastic IP**，重開機後 IP 才不會變。
3. 確認 `http://你的網域` 能打開留言板。

---

## 7. Docker 部署

簡報提供兩種流程，選一種即可。

### 7.1 流程一：透過 Docker Hub（Slide 16）

📌 簡報原文：

```
[Local Machine]                  [Docker Registry]      [EC2 Instance]
Project ──build──▶ Image ──push──▶ Docker Hub ──pull──▶ Image ──run──▶ Container
```

本機 build image → push 到 Docker Hub → EC2 pull image → run container。

💡 指令範例：

```bash
# 本機（EC2 是 x86 時，Apple Silicon Mac 要指定平台）
docker build --platform linux/amd64 -t <帳號>/message-board:latest .
docker push <帳號>/message-board:latest

# EC2
docker pull <帳號>/message-board:latest
docker run -d --name message-board -p 80:8000 --env-file .env --restart always <帳號>/message-board:latest
```

### 7.2 流程二：透過 GitHub（Slide 17）

📌 簡報原文：

```
[Local Machine]   [Git Service]   [EC2 Instance]
Project ──push──▶ GitHub ──pull──▶ Project ──build──▶ Image ──run──▶ Container
```

本機 push 原始碼到 GitHub → EC2 pull 原始碼 → 在 EC2 上 build image → run container。

💡 指令範例：

```bash
# EC2
git clone <repo>   # 之後更新用 git pull
cd <repo>
docker build -t message-board .
docker rm -f message-board 2>/dev/null
docker run -d --name message-board -p 80:8000 --env-file .env --restart always message-board
```

| 比較 | 流程一（Docker Hub） | 流程二（GitHub） |
|---|---|---|
| 在哪裡 build | 本機 | EC2 |
| EC2 需要原始碼 | 否 | 是 |
| 注意事項 | Mac M 系列要 build `linux/amd64` | 小規格 EC2 build 可能較慢、記憶體不足 |

### 7.3 💡 Dockerfile 範例（Python + FastAPI）

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

記得加 `.dockerignore`，排除 `.env`、`.git`、`__pycache__`。

---

## 8. 個人專案：後端方向

📌 簡報原文（Slide 20）：

> **重視資料處理和雲端架構。**
> 記住：我們不是在創業，是否創新、商業模式和市場需求不是重點。

**技術架構**：AWS、Docker、MVC

**可展現的技術亮點**：

- AI 相關的技術整合
- RESTful API 設計
- 資料庫設計和最佳化
- 第三方服務的整合
- 資料擷取、清理、整合
- 快取的規劃和運用
- 多人即時互動
- 高流量架構的測試與實作

---

## 9. 個人專案時程與報告

| 日期 | 項目 |
|---|---|
| **10/12** | 個人專案**期初報告** |
| **10/26** | 個人專案**期中報告** |
| **11/16** | 個人專案**期末報告** |

### 9.1 期初報告內容（10/12）

> 請做一個自己會喜歡的產品。
> ⏱ **6 分鐘提醒，7 分鐘強制結束。**

1. 專案名稱
2. 說明核心的 User Story
3. 初步產出概念品
4. 說明最小可行性範圍
5. Demo 目前的開發成果，並說明使用的技術

### 9.2 準備步驟與關鍵產出

| 步驟 | 內容 | 關鍵產出 |
|---|---|---|
| 專案發想 | 挑戰未知，不要畫地自限；做一個自己會喜歡的產品 | **專案名稱** |
| 初步產出 | 完成初步的網頁和流程；可補充頁面 Wireframe、功能使用流程；設計可參考類似的已上線產品 | **初步的網頁** |
| 專案功能 | 站在使用者角度，最主要使用服務的過程是什麼？產出 1–2 個 User Stories | **User Stories** |
| 最小可行性範圍 | 定義哪些不可或缺；哪些是附加的，沒做完也不影響主要體驗 | **區分主要功能和附加功能** |
| 實作優先順序 | 主要功能一～三（MVP 範圍）→ 附加功能一～三 | **每個功能的優先順序** |

### 9.3 猶豫不決怎麼辦？

> 通常是想法太多無法決定，也可能是在逃避？

- **莫忘初衷。**
- **不要斤斤計較選擇後的得失**：軟體工程本為一體，從哪裡入門沒那麼關鍵。
- **用行動克服猶豫**：如果有 3 個技術選項，就立刻去試這 3 個；不要在沒有實作經驗時空談比較。
