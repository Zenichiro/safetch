from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass

from safetch.config import AppConfig


@dataclass(frozen=True)
class CheckOutcome:
    ok: bool
    status: str
    message: str


def check_proxy_reachable(host: str, port: int, timeout: float) -> CheckOutcome:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return CheckOutcome(True, "proxy_reachable", f"proxy {host}:{port} is reachable")
    except OSError as exc:
        return CheckOutcome(False, "proxy_unreachable", f"proxy {host}:{port} is unreachable: {exc}")


def check_proxy_egress(host: str, port: int, timeout: float, url: str) -> CheckOutcome:
    proxy_url = f"http://{host}:{port}"
    proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    opener = urllib.request.build_opener(proxy_handler)
    request = urllib.request.Request(url=url, method="HEAD")

    try:
        with opener.open(request, timeout=timeout) as response:
            return CheckOutcome(
                True,
                "proxy_egress_ok",
                f"proxy egress check succeeded with status {response.status}",
            )
    except urllib.error.URLError as exc:
        return CheckOutcome(False, "proxy_egress_failed", f"proxy egress check failed: {exc}")


def check_gluetun(host: str, port: int, path: str, timeout: float) -> CheckOutcome:
    url = f"http://{host}:{port}{path}"
    request = urllib.request.Request(url=url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(256).decode("utf-8", errors="replace").strip()
            message = "gluetun control API reachable"
            if body:
                try:
                    parsed = json.loads(body)
                    if isinstance(parsed, dict) and "public_ip" in parsed:
                        message = f"gluetun reports public IP {parsed['public_ip']}"
                except json.JSONDecodeError:
                    pass
            return CheckOutcome(True, "gluetun_ok", message)
    except urllib.error.URLError as exc:
        return CheckOutcome(False, "gluetun_failed", f"gluetun check failed: {exc}")


def run_checks(config: AppConfig) -> list[CheckOutcome]:
    outcomes = [
        check_proxy_reachable(
            host=config.proxy.host,
            port=config.proxy.port,
            timeout=config.checks.connect_timeout,
        ),
        check_proxy_egress(
            host=config.proxy.host,
            port=config.proxy.port,
            timeout=config.checks.connect_timeout,
            url=config.checks.egress_url,
        ),
    ]

    if config.gluetun.enabled:
        outcomes.append(
            check_gluetun(
                host=config.gluetun.host,
                port=config.gluetun.port,
                path=config.gluetun.path,
                timeout=config.checks.connect_timeout,
            )
        )

    return outcomes
