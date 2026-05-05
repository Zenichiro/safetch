from pathlib import Path

from safetch.config import AppConfig, DEFAULT_CONFIG_PATH, load_config


def test_config_defaults_when_file_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.toml")

    assert config == AppConfig()


def test_config_reads_file_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[proxy]
host = "10.0.0.2"
port = 9999

[gluetun]
enabled = false
port = 9000
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.proxy.host == "10.0.0.2"
    assert config.proxy.port == 9999
    assert config.gluetun.enabled is False
    assert config.gluetun.port == 9000


def test_default_config_path_constant() -> None:
    assert str(DEFAULT_CONFIG_PATH).endswith(".config/safetch/config.toml")
