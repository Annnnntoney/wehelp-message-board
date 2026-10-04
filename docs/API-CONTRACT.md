# API 契約：message-board

給頁面（`app/static/index.html`）串接用。錯誤格式統一為 HTTP status + `{ "error", "message" }`，`message` 可直接顯示給使用者。

## `GET /healthz`

健康檢查，給 CI、CD smoke test、第二週的 Load Balancer 用。

```json
{ "status": "ok" }
```

## `GET /`

回傳留言板頁面（HTML）。

## `POST /api/messages`

新增一則圖文留言。

```http
POST /api/messages
Content-Type: multipart/form-data

content=測試看看這個
image=<檔案>
```

| 欄位      | 型別   | 規則                                                  |
| --------- | ------ | ----------------------------------------------------- |
| `content` | string | 必填；去掉首尾空白後 1–1000 字                        |
| `image`   | file   | 必填；`image/jpeg`、`image/png`、`image/webp`、`image/gif`；≤ `MAX_UPLOAD_MB`（預設 5MB） |

處理順序：驗證 → 上傳 S3（key = `uploads/<uuid>.<副檔名>`）→ 寫入 RDS。寫 DB 失敗時刪掉剛上傳的 S3 物件，避免孤兒檔。

### 成功（201）

```json
{
  "data": {
    "id": 4,
    "content": "選擇一張圖片後送出",
    "imageUrl": "https://dxxxx.cloudfront.net/uploads/2f1c...e9.jpg",
    "createdAt": "2026-10-06T14:03:00Z"
  }
}
```

### 錯誤

| Status | `error`              | 情況                         |
| ------ | -------------------- | ---------------------------- |
| 400    | `invalid_content`    | 文字空白或超過 1000 字       |
| 400    | `image_required`     | 沒附圖片                     |
| 413    | `image_too_large`    | 超過大小上限                 |
| 415    | `unsupported_image`  | 不是允許的圖片格式           |
| 502    | `upload_failed`      | S3 上傳失敗                  |
| 500    | `internal_error`     | 資料庫或其他內部錯誤         |

```json
{ "error": "image_too_large", "message": "圖片不能超過 5MB" }
```

FastAPI 預設的 422 驗證錯誤要用 exception handler 轉成上面的 400 格式。5xx 不回傳 AWS 錯誤細節、bucket 名稱或連線字串。

## `GET /api/messages`

列出所有留言，依 `createdAt` **新到舊**（剛送出的在最上面）。

### 成功（200）

```json
{
  "data": [
    {
      "id": 4,
      "content": "選擇一張圖片後送出",
      "imageUrl": "https://dxxxx.cloudfront.net/uploads/2f1c...e9.jpg",
      "createdAt": "2026-10-06T14:03:00Z"
    },
    {
      "id": 3,
      "content": "測試看看這個",
      "imageUrl": "https://dxxxx.cloudfront.net/uploads/a81b...04.jpg",
      "createdAt": "2026-10-06T13:40:00Z"
    }
  ]
}
```

- 沒有留言時回 `{ "data": [] }`。
- `imageUrl` 由 `CLOUDFRONT_DOMAIN` + DB 裡的 `image_key` 組成，不回傳 S3 網址。
- `createdAt` 為 UTC 的 ISO 8601，頁面自行轉台灣時間。
- 第一週不分頁；留言多了再加 `?limit=&before=`。

## 資料表

```sql
CREATE TABLE IF NOT EXISTS messages (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  content     VARCHAR(1000) NOT NULL,
  image_key   VARCHAR(255)  NOT NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_created_at (created_at)
) DEFAULT CHARSET = utf8mb4;
```

`utf8mb4` 才存得了 emoji。
