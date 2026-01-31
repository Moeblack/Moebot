from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .config_schema import MoebotConfig


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    message: str = ""


def _as_path(p: str, *, base_dir: Path) -> Path:
    path = Path(p)
    if path.is_absolute():
        return path
    return base_dir / path


def validate_required_secrets(cfg: MoebotConfig) -> ValidationResult:
    llm_key = cfg.llm.api_key.get_secret_value()
    if not llm_key:
        return ValidationResult(ok=False, message="missing required secret: llm.api_key")
    return ValidationResult(ok=True)


def validate_paths_exist(cfg: MoebotConfig, *, base_dir: Path) -> ValidationResult:
    # UX 设计：在本地/新部署场景，这些目录可以由系统自动创建，不应该阻塞保存。
    # 这里仅做“warning 级”检查：缺失时返回 ok=True，但在 message 中提示。
    missing = []
    for field_name in ("skills_dir", "plugins_dir", "transcripts_dir", "media_dir"):
        value = getattr(cfg.paths, field_name)
        path = _as_path(str(value), base_dir=base_dir)
        if not path.exists():
            missing.append(field_name)
    if missing:
        return ValidationResult(ok=True, message=f"paths not found yet (will be created on demand): {', '.join(missing)}")
    return ValidationResult(ok=True)


def validate_config(cfg: MoebotConfig, *, base_dir: Path) -> ValidationResult:
    # 业务约束：overlap 必须小于 chunk_size
    if cfg.memory.chunk_overlap >= cfg.memory.chunk_size:
        return ValidationResult(ok=False, message="memory.chunk_overlap must be < memory.chunk_size")

    r = validate_paths_exist(cfg, base_dir=base_dir)
    if not r.ok:
        return r
    # 将 paths 的提示信息透传出去（warning 级）
    if r.message:
        return ValidationResult(ok=True, message=r.message)
    return ValidationResult(ok=True)

