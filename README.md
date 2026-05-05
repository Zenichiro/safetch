# safetch

`safetch` is a small VPN-aware `wget` wrapper for safely downloading files through a verified proxy path.

It checks the configured proxy or VPN path before downloading, fails closed if verification fails, and never falls back to a direct connection.

## Features

- Accepts one URL from the CLI or multiple URLs from `--input FILE`
- Uses `wget` as the download backend
- Forces `wget` to use the configured HTTP and HTTPS proxy explicitly
- Refuses to run `wget` if proxy or VPN checks fail
- Supports a generic proxy-only check and an optional Gluetun-aware check
- Resumes downloads by default with `wget --continue`
- Supports `--no-resume`, `-o/--output`, `-d/--output-dir`, `--dry-run`, `--test`, repeatable `--header`, and `--json`
- Redacts credentials in logs and output
- Processes batch input files sequentially and continues after individual failures

## Install

```bash
python -m pip install .
```

## Usage

Single URL:

```bash
safetch https://example.com/file.bin
```

Batch mode:

```bash
safetch --input urls.txt --output-dir downloads
```

Dry run:

```bash
safetch --dry-run https://example.org/archive.zip
```

Add request headers:

```bash
safetch --header "Authorization: Bearer secret-token" https://example.com/file.bin
```

Machine-readable output:

```bash
safetch --json --input urls.txt
```

## Configuration

Default config path:

```text
~/.config/safetch/config.toml
```

Precedence:

1. Built-in defaults
2. Config file
3. Environment variables
4. CLI flags

Environment variables:

- `SAFETCH_PROXY_HOST`
- `SAFETCH_PROXY_PORT`
- `SAFETCH_GLUETUN_ENABLED`
- `SAFETCH_GLUETUN_HOST`
- `SAFETCH_GLUETUN_PORT`
- `SAFETCH_CONNECT_TIMEOUT`
- `SAFETCH_EGRESS_URL`
- `SAFETCH_LOG_ENABLED`

First-time setup:

```bash
safetch init
```

This writes `~/.config/safetch/config.toml` interactively so plain commands like `safetch https://example.com/file.bin` can use your configured proxy by default.

Example config:

```toml
[proxy]
host = "127.0.0.1"
port = 8888

[gluetun]
enabled = false
host = "127.0.0.1"
port = 8000
path = "/v1/publicip/ip"

[checks]
connect_timeout = 5.0
egress_url = "https://example.com/"

[logging]
enabled = false
```

## Behavior

- The proxy reachability check verifies that the configured proxy host and port accept TCP connections.
- The egress check performs a small HTTP request through the configured proxy to confirm internet reachability through that path.
- If Gluetun checks are enabled, `safetch` also validates the Gluetun control API before downloading.
- In batch mode, downloads run sequentially. A failed item does not stop the remaining items, but the final process exit code is non-zero if any item fails.

## Development

```bash
python -m pip install -e .[dev]
python -m pytest
```
