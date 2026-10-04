from fastapi import FastAPI

app = FastAPI(title="message-board")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """給 Docker、CD smoke test、之後的 Load Balancer 用的健康檢查。"""
    return {"status": "ok"}
