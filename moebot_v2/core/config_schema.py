from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, SecretStr

try:  # pydantic v2
    from pydantic import ConfigDict, HttpUrl

    _V2 = True
except Exception:  # pragma: no cover
    from pydantic import AnyUrl as HttpUrl  # type: ignore

    _V2 = False


class _Model(BaseModel):
    if _V2:  # pragma: no cover (branch depends on runtime pydantic)
        model_config = ConfigDict(validate_assignment=True, validate_default=True, extra="forbid")
    else:  # pragma: no cover
        class Config:
            validate_assignment = True
            extra = "forbid"


class LLMConfig(_Model):
    base_url: HttpUrl = "https://generativelanguage.googleapis.com/v1beta"
    api_key: SecretStr = SecretStr("")
    model: str = "gemini-2.0-flash"
    timeout: int = Field(default=30, ge=1, le=300)
    max_tokens: int = Field(default=8192, ge=1, le=200000)


class EmbeddingConfig(_Model):
    base_url: HttpUrl = "https://generativelanguage.googleapis.com/v1beta"
    api_key: SecretStr = SecretStr("")
    model: str = "text-embedding-004"
    dimensions: Optional[int] = Field(default=None, ge=1)
    timeout: int = Field(default=30, ge=1, le=300)


class GatewayConfig(_Model):
    host: str = "0.0.0.0"
    port: int = Field(default=8788, ge=1, le=65535)
    cors_origins: List[str] = Field(default_factory=list)


class NodeHostConfig(_Model):
    host: str = "0.0.0.0"
    port: int = Field(default=8789, ge=1, le=65535)
    gateway_url: str = "http://127.0.0.1:8788"


class MemoryConfig(_Model):
    database_path: str = "data/memory/moebot_v2.db"
    chunk_size: int = Field(default=1200, ge=1, le=20000)
    chunk_overlap: int = Field(default=200, ge=0, le=19999)
    fts_enabled: bool = True


class ContextConfig(_Model):
    budget_chars: int = Field(default=20000, ge=0, le=10_000_000)
    soft_trim_ratio: float = Field(default=0.7, ge=0.0, le=1.0)
    hard_clear_ratio: float = Field(default=0.9, ge=0.0, le=1.0)


class SecurityConfig(_Model):
    sandbox_enabled: bool = True
    sandbox_network: bool = False
    tool_policy: Dict[str, Any] = Field(default_factory=dict)
    exec_approval: bool = True


class PathsConfig(_Model):
    skills_dir: str = "skills"
    plugins_dir: str = "plugins"
    transcripts_dir: str = "data/transcripts"
    media_dir: str = "media"


class MoebotConfig(_Model):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    node_host: NodeHostConfig = Field(default_factory=NodeHostConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)

