import importlib

from fastapi.testclient import TestClient


def make_client(tmp_path, monkeypatch):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('hi')")
    (tmp_path / "index.html").write_text("<div id=root></div>")
    monkeypatch.setenv("STATIC_DIR", str(tmp_path))
    import app.main

    return TestClient(importlib.reload(app.main).app)


def test_serves_frontend_and_api(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/").text == "<div id=root></div>"
    assert client.get("/analyzer").text == "<div id=root></div>"  # SPA fallback
    assert "hi" in client.get("/assets/app.js").text
    assert client.post("/api/analyze-text", json={"resume_text": "Python developer"}).status_code == 200
    assert client.get("/api/missing").status_code == 404


def test_blocks_path_traversal(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    assert client.get("/..%2F..%2Fetc%2Fpasswd").text == "<div id=root></div>"
