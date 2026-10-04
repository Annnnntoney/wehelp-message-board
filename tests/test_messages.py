from unittest.mock import patch

from tests.conftest import BUCKET

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
JPG = b"\xff\xd8\xff" + b"0" * 100


def post(client, content="哈囉", image=PNG, filename="a.png"):
    files = {"image": (filename, image, "image/png")} if image is not None else None
    return client.post("/api/messages", data={"content": content}, files=files)


def test_create_message_uploads_to_s3_and_returns_cdn_url(client, s3):
    res = post(client, content="  測試看看這個  ")

    assert res.status_code == 201
    data = res.json()["data"]
    assert data["content"] == "測試看看這個"
    assert data["imageUrl"].startswith("https://cdn.example.com/uploads/")
    assert data["imageUrl"].endswith(".png")

    key = data["imageUrl"].removeprefix("https://cdn.example.com/")
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    assert obj["ContentType"] == "image/png"


def test_list_messages_newest_first(client):
    post(client, content="第一則")
    post(client, content="第二則", image=JPG, filename="b.jpg")

    res = client.get("/api/messages")

    assert res.status_code == 200
    assert [m["content"] for m in res.json()["data"]] == ["第二則", "第一則"]


def test_list_messages_empty(client):
    assert client.get("/api/messages").json() == {"data": []}


def test_blank_content_rejected(client):
    res = post(client, content="   ")
    assert res.status_code == 400
    assert res.json()["error"] == "invalid_content"


def test_too_long_content_rejected(client):
    res = post(client, content="字" * 1001)
    assert res.status_code == 400


def test_missing_image_rejected(client):
    res = post(client, image=None)
    assert res.status_code == 400
    assert res.json()["error"] == "image_required"


def test_non_image_rejected_even_with_image_filename(client):
    res = post(client, image=b"<script>alert(1)</script>", filename="evil.png")
    assert res.status_code == 415
    assert res.json()["error"] == "unsupported_image"


def test_too_large_image_rejected(client):
    res = post(client, image=PNG + b"0" * (1024 * 1024))
    assert res.status_code == 413
    assert res.json()["error"] == "image_too_large"


def test_db_failure_removes_uploaded_image(client, s3):
    with patch("app.database.insert_message", side_effect=RuntimeError("db down")):
        res = post(client)

    assert res.status_code == 500
    assert res.json()["error"] == "internal_error"
    assert "db down" not in res.text
    assert s3.list_objects_v2(Bucket=BUCKET).get("KeyCount", 0) == 0


def test_index_page_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "發表一篇圖文" in res.text
