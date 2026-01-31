from pathlib import Path

import pytest
from pydantic import ValidationError


def test_url_validation() -> None:
    from moebot_v2.core.config_schema import MoebotConfig

    with pytest.raises(ValidationError):
        MoebotConfig.model_validate({"llm": {"base_url": "not-a-url"}})


def test_port_range() -> None:
    from moebot_v2.core.config_schema import MoebotConfig

    with pytest.raises(ValidationError):
        MoebotConfig.model_validate({"gateway": {"port": 70000}})


def test_path_exists(tmp_path: Path) -> None:
    from moebot_v2.core.config_schema import MoebotConfig
    from moebot_v2.core.config_validators import validate_config

    cfg = MoebotConfig()
    cfg.paths.skills_dir = str(tmp_path / "skills")
    cfg.paths.plugins_dir = str(tmp_path / "plugins")
    cfg.paths.transcripts_dir = str(tmp_path / "data" / "transcripts")
    cfg.paths.media_dir = str(tmp_path / "media")

    res = validate_config(cfg, base_dir=tmp_path)
    assert res.ok is True

    cfg.paths.plugins_dir = str(tmp_path / "plugins_missing")
    res2 = validate_config(cfg, base_dir=tmp_path)
    assert res2.ok is True
    assert "plugins_dir" in (res2.message or "")


def test_api_key_format() -> None:
    from moebot_v2.core.config_schema import MoebotConfig
    from moebot_v2.core.config_validators import validate_required_secrets

    cfg = MoebotConfig()
    cfg.llm.api_key = ""
    res = validate_required_secrets(cfg)
    assert res.ok is False
    assert "llm.api_key" in (res.message or "")

