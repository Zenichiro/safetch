from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

DEFAULT_CONFIG_PATH = Path("~/.config/safetch/config.toml").expanduser()


@dataclass(frozen=True)
class ProxyConfig:
    host: str = "127.0.0.1"
    port: int = 8888


@dataclass(frozen=True)
class GluetunConfig:
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/v1/publicip/ip"


@dataclass(frozen=True)
class CheckConfig:
    connect_timeout: float = 5.0
    egress_url: str = "https://example.com/"


@dataclass(frozen=True)
class LoggingConfig:
    enabled: bool = False


@dataclass(frozen=True)
class AppConfig:
    proxy: ProxyConfig = ProxyConfig()
    gluetun: GluetunConfig = GluetunConfig()
    checks: CheckConfig = CheckConfig()
    logging: LoggingConfig = LoggingConfig()


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _apply_mapping(config: AppConfig, data: dict[str, Any]) -> AppConfig:
    proxy_data = data.get("proxy", {})
    gluetun_data = data.get("gluetun", {})
    checks_data = data.get("checks", {})
    logging_data = data.get("logging", {})

    return AppConfig(
        proxy=ProxyConfig(
            host=proxy_data.get("host", config.proxy.host),
            port=int(proxy_data.get("port", config.proxy.port)),
        ),
        gluetun=GluetunConfig(
            enabled=bool(gluetun_data.get("enabled", config.gluetun.enabled)),
            host=gluetun_data.get("host", config.gluetun.host),
            port=int(gluetun_data.get("port", config.gluetun.port)),
            path=gluetun_data.get("path", config.gluetun.path),
        ),
        checks=CheckConfig(
            connect_timeout=float(checks_data.get("connect_timeout", config.checks.connect_timeout)),
            egress_url=checks_data.get("egress_url", config.checks.egress_url),
        ),
        logging=LoggingConfig(
            enabled=bool(logging_data.get("enabled", config.logging.enabled)),
        ),
    )


def _apply_environment(config: AppConfig) -> AppConfig:
    proxy = replace(
        config.proxy,
        host=os.getenv("SAFETCH_PROXY_HOST", config.proxy.host),
        port=int(os.getenv("SAFETCH_PROXY_PORT", str(config.proxy.port))),
    )
    gluetun = replace(
        config.gluetun,
        enabled=_parse_bool(os.getenv("SAFETCH_GLUETUN_ENABLED", str(config.gluetun.enabled))),
        host=os.getenv("SAFETCH_GLUETUN_HOST", config.gluetun.host),
        port=int(os.getenv("SAFETCH_GLUETUN_PORT", str(config.gluetun.port))),
    )
    checks = replace(
        config.checks,
        connect_timeout=float(
            os.getenv("SAFETCH_CONNECT_TIMEOUT", str(config.checks.connect_timeout))
        ),
        egress_url=os.getenv("SAFETCH_EGRESS_URL", config.checks.egress_url),
    )
    logging = replace(
        config.logging,
        enabled=_parse_bool(os.getenv("SAFETCH_LOG_ENABLED", str(config.logging.enabled))),
    )
    return AppConfig(proxy=proxy, gluetun=gluetun, checks=checks, logging=logging)


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    config = AppConfig()
    config = _apply_mapping(config, _load_toml(path))
    config = _apply_environment(config)
    return config
