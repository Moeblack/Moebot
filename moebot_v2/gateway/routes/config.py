from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from moebot_v2.core.config_schema import MoebotConfig
from moebot_v2.core.config_store import ConfigStore
from moebot_v2.core.config_validators import validate_config, validate_required_secrets


class UpdateResponse(BaseModel):
    success: bool
    message: str = ""


class TestResponse(BaseModel):
    ok: bool
    status_code: int | None = None
    message: str = ""


class ExportResponse(BaseModel):
    yaml: str
    masked: Dict[str, Any]


class ImportRequest(BaseModel):
    config: Dict[str, Any]


def create_config_router(*, store: ConfigStore, base_dir: Path) -> APIRouter:
    router = APIRouter(tags=["config-v2"])

    def _deep_merge(a: dict, b: dict) -> dict:
        # b 覆盖 a
        out = dict(a)
        for k, v in (b or {}).items():
            if isinstance(out.get(k), dict) and isinstance(v, dict):
                out[k] = _deep_merge(out[k], v)
            else:
                out[k] = v
        return out

    @router.get("/config")
    def get_config(masked: bool = True) -> Dict[str, Any]:
        return store.get_masked() if masked else store.get_unmasked()

    @router.get("/config/schema")
    def get_schema() -> Dict[str, Any]:
        return MoebotConfig.model_json_schema()

    @router.patch("/config/{section}")
    def update_section(section: str, data: Dict[str, Any]) -> UpdateResponse:
        section = section.strip()
        base = store.get_unmasked()

        if section not in base:
            raise HTTPException(status_code=404, detail="unknown section")

        merged = {**base, section: _deep_merge(base.get(section) or {}, data or {})}
        try:
            cfg = MoebotConfig.model_validate(merged)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 业务验证（paths 等）
        r = validate_config(cfg, base_dir=base_dir)
        if not r.ok:
            raise HTTPException(status_code=400, detail=r.message)

        # 保存并返回
        store.save(cfg)
        return UpdateResponse(success=True, message="ok")

    @router.post("/config/test/{section}")
    def test_connection(section: str) -> TestResponse:
        tr = store.test_connection(section)
        return TestResponse(ok=tr.ok, status_code=tr.status_code, message=tr.message)

    @router.get("/config/export")
    def export_config() -> ExportResponse:
        masked = store.get_masked()
        # 导出 YAML（非敏感）
        yaml_text = yaml.safe_dump(
            {k: v for k, v in store.get_unmasked().items() if k != "llm" and k != "embeddings"}
            | {
                "llm": {k: v for k, v in store.get_unmasked().get("llm", {}).items() if k != "api_key"},
                "embeddings": {
                    k: v for k, v in store.get_unmasked().get("embeddings", {}).items() if k != "api_key"
                },
            },
            allow_unicode=True,
            sort_keys=False,
        )
        return ExportResponse(yaml=yaml_text, masked=masked)

    @router.post("/config/import")
    def import_config(req: ImportRequest) -> UpdateResponse:
        base = store.get_unmasked()
        merged = _deep_merge(base, req.config)
        try:
            cfg = MoebotConfig.model_validate(merged)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        r = validate_config(cfg, base_dir=base_dir)
        if not r.ok:
            raise HTTPException(status_code=400, detail=r.message)

        # 允许导入时暂时缺少 key（由 UI 再补）；如果你希望强制，改为 validate_required_secrets
        store.save(cfg)
        return UpdateResponse(success=True, message="ok")

    @router.get("/config/{section}")
    def get_section(section: str) -> Dict[str, Any]:
        # 注意：此路由必须放在最后，避免吞掉 /config/export 等静态路由
        section = section.strip()
        cfg = store.get_masked()
        if section not in cfg:
            raise HTTPException(status_code=404, detail="unknown section")
        return cfg[section]

    return router

