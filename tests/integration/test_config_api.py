from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_app(tmp_path: Path):
    from moebot_v2.core.config_store import ConfigStore
    from moebot_v2.gateway.routes.config import create_config_router

    store = ConfigStore(yaml_path=tmp_path / "config_v2.yaml", env_path=tmp_path / ".env")
    app = FastAPI()
    app.include_router(create_config_router(store=store, base_dir=tmp_path), prefix="/api/v2")
    return app, store


def test_get_config(tmp_path: Path) -> None:
    app, store = _make_app(tmp_path)
    store.load()

    client = TestClient(app)
    resp = client.get("/api/v2/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm" in data
    assert data["llm"]["api_key"] in ("", "****")


def test_get_section(tmp_path: Path) -> None:
    app, store = _make_app(tmp_path)
    store.load()

    client = TestClient(app)
    resp = client.get("/api/v2/config/llm")
    assert resp.status_code == 200
    data = resp.json()
    assert "base_url" in data


def test_update_section(tmp_path: Path) -> None:
    app, store = _make_app(tmp_path)
    store.load()

    client = TestClient(app)
    resp = client.patch("/api/v2/config/llm", json={"model": "gemini-updated"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 再读回，确保已落盘
    cfg = store.load()
    assert cfg.llm.model == "gemini-updated"


def test_test_connection(tmp_path: Path, monkeypatch) -> None:
    app, store = _make_app(tmp_path)
    store.load()

    from moebot_v2.core.config_store import TestResult

    def _fake_test_connection(section: str):
        return TestResult(ok=True, status_code=200, message="ok")

    monkeypatch.setattr(store, "test_connection", _fake_test_connection, raising=False)

    client = TestClient(app)
    resp = client.post("/api/v2/config/test/llm")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_export_config(tmp_path: Path) -> None:
    app, store = _make_app(tmp_path)
    store.load()

    client = TestClient(app)
    resp = client.get("/api/v2/config/export")
    assert resp.status_code == 200
    data = resp.json()
    assert "yaml" in data


def test_import_config(tmp_path: Path) -> None:
    app, store = _make_app(tmp_path)
    store.load()

    client = TestClient(app)
    resp = client.post("/api/v2/config/import", json={"config": {"gateway": {"port": 9998}}})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert store.load().gateway.port == 9998

