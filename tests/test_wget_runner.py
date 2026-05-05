from safetch.config import AppConfig, ProxyConfig
from safetch.wget_runner import WgetRequest, build_wget_command


def test_build_wget_command_uses_explicit_proxy_and_resume() -> None:
    config = AppConfig(proxy=ProxyConfig(host="127.0.0.1", port=8888))
    request = WgetRequest(
        url="https://example.com/file.bin",
        output="out.bin",
        output_dir="downloads",
        headers=("X-Test: value",),
        resume=True,
    )

    command = build_wget_command(config, request)

    assert command[:7] == [
        "wget",
        "--execute",
        "use_proxy=yes",
        "--execute",
        "http_proxy=http://127.0.0.1:8888",
        "--execute",
        "https_proxy=http://127.0.0.1:8888",
    ]
    assert "--continue" in command
    assert ["--output-document", "out.bin"] == command[8:10]
    assert "https://example.com/file.bin" == command[-1]


def test_build_wget_command_omits_continue_when_disabled() -> None:
    command = build_wget_command(
        AppConfig(),
        WgetRequest(url="https://example.org/archive.zip", resume=False),
    )
    assert "--continue" not in command
