from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import httpx
import yaml
from dotenv import dotenv_values, set_key

from .config_schema import MoebotConfig


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    message: str = ""
    details: Optional[dict] = None


@dataclass(frozen=True)
class TestResult:
    ok: bool
    status_code: Optional[int] = None
    message: str = ""


def _safe_read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _mtime_or_none(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return None


def _deep_set(d: dict, keys: Tuple[str, ...], value: Any) -> None:
    cur = d
    for k in keys[:-1]:
        if k not in cur or not isinstance(cur[k], dict):
            cur[k] = {}
        cur = cur[k]
    cur[keys[-1]] = value


def _deep_get(d: dict, keys: Tuple[str, ...]) -> Any:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def _remove_sensitive(d: dict) -> dict:
    # 只要字段名叫 api_key，就认为敏感，不落盘到 YAML
    def walk(x: Any) -> Any:
        if isinstance(x, dict):
            out = {}
            for k, v in x.items():
                if k == "api_key":
                    continue
                out[k] = walk(v)
            return out
        if isinstance(x, list):
            return [walk(i) for i in x]
        return x

    return walk(d)


class ConfigStore:
    """
    Moebot V2 配置存储层：
    - 非敏感配置：YAML（默认 `config_v2.yaml`）
    - 敏感配置（如 API Key）：.env（默认 `.env`）

    Env 覆盖 YAML，兼容 legacy 的 GEMINI_* 变量读取。
    """

    def __init__(self, *, yaml_path: Path, env_path: Path):
        self.yaml_path = Path(yaml_path)
        self.env_path = Path(env_path)

        self._cached: Optional[MoebotConfig] = None
        self._last_yaml_mtime: Optional[float] = None
        self._last_env_mtime: Optional[float] = None

    def load(self) -> MoebotConfig:
        raw_yaml = self._load_yaml_dict()
        raw_env = self._load_env_dict()

        merged = self._merge(raw_yaml, raw_env)
        cfg = self._validate_to_model(merged)

        self._cached = cfg
        self._last_yaml_mtime = _mtime_or_none(self.yaml_path)
        self._last_env_mtime = _mtime_or_none(self.env_path)
        return cfg

    def save(self, config: MoebotConfig) -> None:
        # YAML：去掉敏感字段
        raw = self._model_to_dict(config)
        raw_non_sensitive = _remove_sensitive(raw)
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)
        self.yaml_path.write_text(
            yaml.safe_dump(raw_non_sensitive, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        # .env：写入敏感字段（目前只写 LLM/Embedding api_key）
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.env_path.exists():
            self.env_path.write_text("", encoding="utf-8")

        llm_key = config.llm.api_key.get_secret_value()
        emb_key = config.embeddings.api_key.get_secret_value()
        if llm_key:
            set_key(str(self.env_path), "MOEBOT_LLM_API_KEY", llm_key, quote_mode="never")
        if emb_key:
            set_key(str(self.env_path), "MOEBOT_EMBED_API_KEY", emb_key, quote_mode="never")

        # 更新缓存
        self._cached = config
        self._last_yaml_mtime = _mtime_or_none(self.yaml_path)
        self._last_env_mtime = _mtime_or_none(self.env_path)

    def reload_if_changed(self) -> bool:
        yaml_m = _mtime_or_none(self.yaml_path)
        env_m = _mtime_or_none(self.env_path)
        changed = (yaml_m != self._last_yaml_mtime) or (env_m != self._last_env_mtime)
        if not changed:
            return False
        self.load()
        return True

    def get_masked(self) -> dict:
        cfg = self._cached or self.load()
        d = self._model_to_dict(cfg)

        def mask(x: Any) -> Any:
            if isinstance(x, dict):
                out = {}
                for k, v in x.items():
                    if k == "api_key":
                        out[k] = "****" if (v or "") else ""
                    else:
                        out[k] = mask(v)
                return out
            if isinstance(x, list):
                return [mask(i) for i in x]
            return x

        return mask(d)

    def get_unmasked(self) -> dict:
        cfg = self._cached or self.load()
        return self._model_to_dict(cfg)

    def validate(self, partial: dict) -> ValidationResult:
        try:
            cfg = self._cached or self.load()
            base = self._model_to_dict(cfg)
            merged = self._merge(base, partial)
            self._validate_to_model(merged)
            return ValidationResult(ok=True)
        except Exception as e:  # pragma: no cover
            return ValidationResult(ok=False, message=str(e))

    def test_connection(self, section: str) -> TestResult:
        """
        连接测试只验证“可达性/基本可用性”，不强依赖特定供应商的健康检查接口。
        - 对 llm/embeddings：对 base_url 做一次 GET（失败则认为不可达）
        """
        section = section.strip().lower()
        if section not in {"llm", "embeddings"}:
            return TestResult(ok=False, message=f"unknown section: {section}")

        cfg = self._cached or self.load()
        url = str(cfg.llm.base_url if section == "llm" else cfg.embeddings.base_url)
        try:
            with httpx.Client(timeout=5.0, follow_redirects=True) as client:
                resp = client.get(url)
            return TestResult(ok=True, status_code=resp.status_code, message="reachable")
        except Exception as e:
            return TestResult(ok=False, message=str(e))

    # -----------------------
    # internals
    # -----------------------

    def _load_yaml_dict(self) -> dict:
        if not self.yaml_path.exists():
            return {}
        text = _safe_read_text(self.yaml_path).strip()
        if not text:
            return {}
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}

    def _load_env_dict(self) -> dict:
        env_raw = {k: v for k, v in (dotenv_values(self.env_path) or {}).items() if v is not None}

        # 兼容旧变量名（读取）
        if "MOEBOT_LLM_API_KEY" not in env_raw and "GEMINI_API_KEY" in env_raw:
            env_raw["MOEBOT_LLM_API_KEY"] = env_raw["GEMINI_API_KEY"]
        if "MOEBOT_LLM_BASE_URL" not in env_raw and "GEMINI_URL" in env_raw:
            env_raw["MOEBOT_LLM_BASE_URL"] = env_raw["GEMINI_URL"]

        # 映射为结构化 dict
        mapped: dict = {}
        mapping: Dict[str, Tuple[str, ...]] = {
            "MOEBOT_LLM_BASE_URL": ("llm", "base_url"),
            "MOEBOT_LLM_MODEL": ("llm", "model"),
            "MOEBOT_LLM_TIMEOUT": ("llm", "timeout"),
            "MOEBOT_LLM_MAX_TOKENS": ("llm", "max_tokens"),
            "MOEBOT_LLM_API_KEY": ("llm", "api_key"),
            "MOEBOT_EMBED_BASE_URL": ("embeddings", "base_url"),
            "MOEBOT_EMBED_MODEL": ("embeddings", "model"),
            "MOEBOT_EMBED_TIMEOUT": ("embeddings", "timeout"),
            "MOEBOT_EMBED_DIMENSIONS": ("embeddings", "dimensions"),
            "MOEBOT_EMBED_API_KEY": ("embeddings", "api_key"),
            "MOEBOT_GATEWAY_HOST": ("gateway", "host"),
            "MOEBOT_GATEWAY_PORT": ("gateway", "port"),
            "MOEBOT_NODE_HOST": ("node_host", "host"),
            "MOEBOT_NODE_PORT": ("node_host", "port"),
            "MOEBOT_GATEWAY_URL": ("node_host", "gateway_url"),
        }

        for key, path in mapping.items():
            if key not in env_raw:
                continue
            v: Any = env_raw[key]
            # 轻量类型转换
            if path[-1] in {"port", "timeout", "max_tokens", "dimensions"}:
                try:
                    v = int(str(v))
                except Exception:
                    pass
            if path[-1] in {"sandbox_enabled", "sandbox_network", "exec_approval"}:
                v = str(v).lower() in {"1", "true", "yes", "on"}
            _deep_set(mapped, path, v)

        return mapped

    def _merge(self, base: dict, override: dict) -> dict:
        # 递归 merge：override 覆盖 base
        def rec(a: Any, b: Any) -> Any:
            if isinstance(a, dict) and isinstance(b, dict):
                out = dict(a)
                for k, v in b.items():
                    out[k] = rec(out.get(k), v)
                return out
            return b if b is not None else a

        return rec(base or {}, override or {})

    def _validate_to_model(self, data: dict) -> MoebotConfig:
        try:
            # pydantic v2
            return MoebotConfig.model_validate(data)  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover
            return MoebotConfig.parse_obj(data)  # type: ignore[attr-defined]

    def _model_to_dict(self, cfg: MoebotConfig) -> dict:
        try:
            d = cfg.model_dump(mode="json")  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover
            d = cfg.dict()

        # SecretStr 在 dump 时可能变成 **********，这里强制改成真实值（再由上层决定是否 mask）
        # 只处理当前 schema 中的 api_key 字段
        for section in ("llm", "embeddings"):
            api_key = _deep_get(d, (section, "api_key"))
            if api_key == "**********":
                # 如果出现遮蔽值，用 model 的真实 secret 值替换
                real = getattr(getattr(cfg, section), "api_key").get_secret_value()
                _deep_set(d, (section, "api_key"), real)
        return d

