from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from safetch.config import AppConfig, load_config
from safetch.input_file import parse_input_file
from safetch.redact import redact_header, redact_text, redact_url
from safetch.result import DownloadResult
from safetch.vpncheck import run_checks
from safetch.wget_runner import WgetRequest, build_wget_command, run_wget

app = typer.Typer(add_completion=False, help="Safely download files through a verified proxy path.")


def _resolve_urls(url: str | None, input_file: Path | None) -> list[str]:
    if bool(url) == bool(input_file):
        raise typer.BadParameter("provide exactly one URL or --input FILE")
    if url:
        return [url]
    assert input_file is not None
    return parse_input_file(input_file)


def _apply_cli_overrides(
    config: AppConfig,
    proxy_host: str | None,
    proxy_port: int | None,
    gluetun_enabled: bool | None,
    gluetun_host: str | None,
    gluetun_port: int | None,
    log_enabled: bool | None,
) -> AppConfig:
    proxy = config.proxy
    gluetun = config.gluetun
    logging = config.logging

    if proxy_host is not None:
        proxy = type(proxy)(host=proxy_host, port=proxy.port)
    if proxy_port is not None:
        proxy = type(proxy)(host=proxy.host, port=proxy_port)
    if gluetun_enabled is not None:
        gluetun = type(gluetun)(
            enabled=gluetun_enabled,
            host=gluetun.host,
            port=gluetun.port,
            path=gluetun.path,
        )
    if gluetun_host is not None:
        gluetun = type(gluetun)(
            enabled=gluetun.enabled,
            host=gluetun_host,
            port=gluetun.port,
            path=gluetun.path,
        )
    if gluetun_port is not None:
        gluetun = type(gluetun)(
            enabled=gluetun.enabled,
            host=gluetun.host,
            port=gluetun_port,
            path=gluetun.path,
        )
    if log_enabled is not None:
        logging = type(logging)(enabled=log_enabled)

    return AppConfig(proxy=proxy, gluetun=gluetun, checks=config.checks, logging=logging)


def _emit(message: str, *, enabled: bool, error: bool = False) -> None:
    if not enabled:
        return
    stream = sys.stderr if error else sys.stdout
    print(redact_text(message), file=stream)


def _result_from_check_failure(url: str, message: str) -> DownloadResult:
    return DownloadResult(
        url=redact_url(url),
        ok=False,
        checks_passed=False,
        attempted_download=False,
        exit_code=2,
        status="checks_failed",
        message=message,
    )


@app.command()
def main(
    url: Annotated[str | None, typer.Argument(help="Single URL to download.")] = None,
    input_file: Annotated[Path | None, typer.Option("--input", help="Read URLs from a file.")] = None,
    output: Annotated[str | None, typer.Option("-o", "--output", help="Output file for a single URL.")] = None,
    output_dir: Annotated[str | None, typer.Option("-d", "--output-dir", help="Output directory.")] = None,
    no_resume: Annotated[bool, typer.Option("--no-resume", help="Disable resume support.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", "--test", help="Run checks without downloading.")] = False,
    header: Annotated[list[str] | None, typer.Option("--header", help="Repeatable request header.")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable final results.")] = False,
    config_path: Annotated[Path | None, typer.Option("--config", help="Override config path.")] = None,
    proxy_host: Annotated[str | None, typer.Option("--proxy-host", help="Proxy host override.")] = None,
    proxy_port: Annotated[int | None, typer.Option("--proxy-port", help="Proxy port override.")] = None,
    gluetun_enabled: Annotated[bool | None, typer.Option("--gluetun/--no-gluetun", help="Enable or disable Gluetun checks.")] = None,
    gluetun_host: Annotated[str | None, typer.Option("--gluetun-host", help="Gluetun host override.")] = None,
    gluetun_port: Annotated[int | None, typer.Option("--gluetun-port", help="Gluetun port override.")] = None,
    log_enabled: Annotated[bool | None, typer.Option("--log/--no-log", help="Enable simple logs.")] = None,
) -> None:
    headers = tuple(header or [])
    config = load_config(config_path)
    config = _apply_cli_overrides(
        config,
        proxy_host=proxy_host,
        proxy_port=proxy_port,
        gluetun_enabled=gluetun_enabled,
        gluetun_host=gluetun_host,
        gluetun_port=gluetun_port,
        log_enabled=log_enabled,
    )

    urls = _resolve_urls(url, input_file)

    if output and len(urls) != 1:
        raise typer.BadParameter("--output can only be used with a single URL")

    check_outcomes = run_checks(config)
    failed_checks = [item for item in check_outcomes if not item.ok]

    if failed_checks:
        message = "; ".join(outcome.message for outcome in failed_checks)
        results = [_result_from_check_failure(item, message) for item in urls]
        _emit(message, enabled=config.logging.enabled, error=True)
        _finish(results, json_output=json_output)
        raise typer.Exit(code=2)

    if dry_run:
        results = [
            DownloadResult(
                url=redact_url(item),
                ok=True,
                checks_passed=True,
                attempted_download=False,
                exit_code=0,
                status="dry_run_ok",
                message="checks passed; download skipped",
            )
            for item in urls
        ]
        _finish(results, json_output=json_output)
        raise typer.Exit(code=0)

    results: list[DownloadResult] = []

    for item in urls:
        request = WgetRequest(
            url=item,
            output=output,
            output_dir=output_dir,
            headers=headers,
            resume=not no_resume,
        )
        command = build_wget_command(config, request)
        redacted_preview = [redact_header(redact_url(part)) for part in command]
        _emit(f"running {' '.join(redacted_preview)}", enabled=config.logging.enabled)
        completed = run_wget(command)
        stderr_text = redact_text(completed.stderr.strip())
        stdout_text = redact_text(completed.stdout.strip())
        message = stderr_text or stdout_text or None
        ok = completed.returncode == 0

        results.append(
            DownloadResult(
                url=redact_url(item),
                ok=ok,
                checks_passed=True,
                attempted_download=True,
                exit_code=completed.returncode,
                status="downloaded" if ok else "download_failed",
                message=message,
                command_preview=redacted_preview,
            )
        )

    exit_code = 0 if all(result.ok for result in results) else 1
    _finish(results, json_output=json_output)
    raise typer.Exit(code=exit_code)


def _finish(results: list[DownloadResult], *, json_output: bool) -> None:
    if json_output:
        payload = [item.to_dict() for item in results]
        print(json.dumps(payload, indent=2))
        return

    for result in results:
        line = f"[{result.status}] {result.url}"
        if result.message:
            line = f"{line} :: {result.message}"
        print(redact_text(line))
