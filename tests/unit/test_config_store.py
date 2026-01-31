import time
from pathlib import Path

import pytest


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_from_env(tmp_path: Path) -> None:
    from moebot_v2.core.config_store import ConfigStore

    env_path = tmp_path / ".env"
    yaml_path = tmp_path / "config_v2.yaml"

    _write_text(
        env_path,
        "\n".join(
            [
                "MOEBOT_LLM_API_KEY=abc",
                "MOEBOT_LLM_BASE_URL=https://example.com/v1beta",
                "MOEBOT_LLM_MODEL=gemini-test",
                "MOEBOT_EMBED_API_KEY=emb_abc",
                "",
            ]
        ),
    )

    store = ConfigStore(yaml_path=yaml_path, env_path=env_path)
    cfg = store.load()

    assert cfg.llm.api_key.get_secret_value() == "abc"
    assert str(cfg.llm.base_url).startswith("https://example.com/")
    assert cfg.llm.model == "gemini-test"
    assert cfg.embeddings.api_key.get_secret_value() == "emb_abc"


def test_load_from_yaml(tmp_path: Path) -> None:
    from moebot_v2.core.config_store import ConfigStore

    env_path = tmp_path / ".env"
    yaml_path = tmp_path / "config_v2.yaml"

    _write_text(
        yaml_path,
        "\n".join(
            [
                "llm:",
                "  base_url: https://example.com/v1beta",
                "  model: gemini-from-yaml",
                "gateway:",
                "  host: 0.0.0.0",
                "  port: 8788",
                "",
            ]
        ),
    )

    store = ConfigStore(yaml_path=yaml_path, env_path=env_path)
    cfg = store.load()

    assert str(cfg.llm.base_url).startswith("https://example.com/")
    assert cfg.llm.model == "gemini-from-yaml"
    assert cfg.gateway.host == "0.0.0.0"
    assert cfg.gateway.port == 8788


def test_merge_priority_env_over_yaml(tmp_path: Path) -> None:
    from moebot_v2.core.config_store import ConfigStore

    env_path = tmp_path / ".env"
    yaml_path = tmp_path / "config_v2.yaml"

    _write_text(
        yaml_path,
        "\n".join(
            [
                "llm:",
                "  base_url: https://yaml.example/v1beta",
                "  model: gemini-yaml",
                "",
            ]
        ),
    )
    _write_text(
        env_path,
        "\n".join(
            [
                "MOEBOT_LLM_BASE_URL=https://env.example/v1beta",
                "MOEBOT_LLM_MODEL=gemini-env",
                "",
            ]
        ),
    )

    store = ConfigStore(yaml_path=yaml_path, env_path=env_path)
    cfg = store.load()

    assert str(cfg.llm.base_url).startswith("https://env.example/")
    assert cfg.llm.model == "gemini-env"


def test_save_to_yaml_and_env(tmp_path: Path) -> None:
    from moebot_v2.core.config_schema import MoebotConfig
    from moebot_v2.core.config_store import ConfigStore

    env_path = tmp_path / ".env"
    yaml_path = tmp_path / "config_v2.yaml"

    store = ConfigStore(yaml_path=yaml_path, env_path=env_path)
    cfg = MoebotConfig()
    cfg.llm.base_url = "https://save.example/v1beta"
    cfg.llm.model = "gemini-save"
    cfg.llm.api_key = "save_key"

    store.save(cfg)

    assert yaml_path.exists()
    assert "save_key" not in yaml_path.read_text(encoding="utf-8")
    assert "gemini-save" in yaml_path.read_text(encoding="utf-8")

    assert env_path.exists()
    env_text = env_path.read_text(encoding="utf-8")
    assert "MOEBOT_LLM_API_KEY=save_key" in env_text


def test_hot_reload_detection(tmp_path: Path) -> None:
    from moebot_v2.core.config_store import ConfigStore

    env_path = tmp_path / ".env"
    yaml_path = tmp_path / "config_v2.yaml"

    _write_text(yaml_path, "gateway:\n  host: 127.0.0.1\n  port: 8788\n")
    store = ConfigStore(yaml_path=yaml_path, env_path=env_path)
    store.load()

    # 确保 mtime 有变化
    time.sleep(0.01)
    _write_text(yaml_path, "gateway:\n  host: 127.0.0.1\n  port: 9999\n")

    assert store.reload_if_changed() is True
    cfg = store.load()
    assert cfg.gateway.port == 9999


def test_sensitive_mask(tmp_path: Path) -> None:
    from moebot_v2.core.config_store import ConfigStore

    env_path = tmp_path / ".env"
    yaml_path = tmp_path / "config_v2.yaml"

    _write_text(env_path, "MOEBOT_LLM_API_KEY=abc\n")
    store = ConfigStore(yaml_path=yaml_path, env_path=env_path)
    store.load()

    masked = store.get_masked()
    assert masked["llm"]["api_key"] == "****"
