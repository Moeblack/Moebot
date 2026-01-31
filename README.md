# Moebot V2 配置中心（局域网）

这个仓库当前默认只保留 **V2 配置中心**，用于在局域网中管理 Moebot V2 的关键配置：

- LLM / Embedding（Base URL、Model、API Key）
- Gateway / Node-Host（host/port/gateway_url）
- Memory / Context / Security / Paths 等

旧版（V1）实现已归档到 [`legacy_v1/`](legacy_v1/README.md)，仅供参考，不再作为运行入口。

## 启动

### 1) 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 准备环境变量

复制 `.env.example` 为 `.env` 并填写必要的 Key：

```bash
cp .env.example .env
```

### 3) 运行配置中心

```bash
python scripts/monitor_web.py
```

默认监听 `0.0.0.0:8000`，浏览器打开：

- `http://<你的服务器IP>:8000`

## API

- `GET /api/v2/config`：获取配置（默认 masked）
- `PATCH /api/v2/config/{section}`：更新分组
- `GET /api/v2/config/schema`：获取 schema（前端自动渲染表单）

