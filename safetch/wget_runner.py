from __future__ import annotations

import subprocess
from dataclasses import dataclass

from safetch.config import AppConfig


@dataclass(frozen=True)
class WgetRequest:
    url: str
    output: str | None = None
    output_dir: str | None = None
    headers: tuple[str, ...] = ()
    resume: bool = True


def build_wget_command(config: AppConfig, request: WgetRequest) -> list[str]:
    proxy_url = f"http://{config.proxy.host}:{config.proxy.port}"

    command = [
        "wget",
        "--content-disposition",
        "--execute",
        "use_proxy=yes",
        "--execute",
        f"http_proxy={proxy_url}",
        "--execute",
        f"https_proxy={proxy_url}",
    ]

    if request.resume:
        command.append("--continue")

    if request.output:
        command.extend(["--output-document", request.output])

    if request.output_dir:
        command.extend(["--directory-prefix", request.output_dir])

    for header in request.headers:
        command.extend(["--header", header])

    command.append(request.url)
    return command


def run_wget(command: list[str], *, stream_output: bool = False) -> subprocess.CompletedProcess[str]:
    if stream_output:
        completed = subprocess.run(command, check=False)
        return subprocess.CompletedProcess(
            args=command,
            returncode=completed.returncode,
            stdout=None,
            stderr=None,
        )

    return subprocess.run(command, capture_output=True, text=True, check=False)
