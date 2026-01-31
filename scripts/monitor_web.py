"""
Moebot V2 配置中心（Web UI）

只提供 V2 配置中心：
- Web UI: GET /
- API: /api/v2/config/*

说明：
这个进程只负责“局域网配置中心”，不再承载 V1 的监控/人格/记忆等页面与接口。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# 确保仓库根目录可 import（用于 moebot_v2/）
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from moebot_v2.core.config_store import ConfigStore  # noqa: E402
from moebot_v2.gateway.routes.config import create_config_router  # noqa: E402

app = FastAPI(title="Moebot V2 Config Center")

app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))

store = ConfigStore(yaml_path=ROOT_DIR / "config_v2.yaml", env_path=ROOT_DIR / ".env")
app.include_router(create_config_router(store=store, base_dir=ROOT_DIR), prefix="/api/v2")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    return {"ok": True}


if __name__ == "__main__":
    host = os.getenv("MOEBOT_CONFIG_HOST", "0.0.0.0")
    port = int(os.getenv("MOEBOT_CONFIG_PORT", "8000"))
    uvicorn.run("scripts.monitor_web:app", host=host, port=port, reload=False)

