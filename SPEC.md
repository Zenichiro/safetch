# safetch v0.1 Specification

## Goal

`safetch` is a small command-line wrapper around `wget` for downloading files only after a proxy or VPN-backed proxy path has been verified.

The core safety property is fail-closed behavior:

- If proxy or VPN verification fails, `safetch` exits before invoking `wget`.
- `safetch` never performs a direct fallback download.

## Scope

v0.1 includes:

- Single URL input from the CLI
- Batch URL input with `--input FILE`
- Sequential batch downloads only
- Explicit proxy configuration for `wget`
- Proxy connectivity and egress checks
- Optional Gluetun-aware verification
- Download resume enabled by default
- Simple optional logging
- JSON final results
- Secret redaction in output

v0.1 excludes:

- Parallel downloads
- Pluggable downloader backends
- Advanced retry orchestration
- Persistent job tracking

## Inputs

Exactly one of the following input modes must be used:

- One positional URL
- `--input FILE`

Batch input file rules:

- Ignore blank lines
- Ignore lines beginning with `#`
- Preserve remaining lines as URLs in order

## Configuration

Default config path:

`~/.config/safetch/config.toml`

Configuration precedence:

1. Built-in defaults
2. Config file
3. Environment variables
4. CLI flags

Built-in defaults:

- Proxy host: `127.0.0.1`
- Proxy port: `8888`
- Gluetun host: `127.0.0.1`
- Gluetun port: `8000`
- Gluetun enabled: `true`
- Connect timeout: `5.0`
- Egress URL: `https://example.com/`
- Logging enabled: `false`
- Resume enabled: `true`

## Checks

### Generic proxy checks

Before any download, `safetch` must:

1. Verify the configured proxy host and port are reachable over TCP.
2. Perform a small HTTP request through that proxy to verify internet egress through the proxy path.

If either check fails, the download is rejected.

### Gluetun-aware check

When enabled, `safetch` must also query the Gluetun control API.

The check succeeds only if the control API responds successfully.

This checker is optional and configurable so future proxy-aware VPN containers can be added without changing the batch or `wget` flow.

## Download execution

`wget` is the only download backend in v0.1.

`safetch` must invoke `wget` with explicit proxy configuration:

- `--execute use_proxy=yes`
- `--execute http_proxy=http://HOST:PORT`
- `--execute https_proxy=http://HOST:PORT`

It must not rely only on inherited shell proxy environment variables.

Default download behavior:

- Use `wget --continue`

If `--no-resume` is set:

- Omit `--continue`

Single-file output:

- `-o/--output` maps to `wget --output-document`

Output directory:

- `-d/--output-dir` maps to `wget --directory-prefix`

Headers:

- Each `--header "Key: Value"` becomes a distinct `wget --header` argument

## Dry-run behavior

`--dry-run` and `--test` are aliases.

In dry-run mode:

- Run all configured checks
- Do not invoke `wget`
- Return success only if checks pass

## Results and exit codes

Per-URL results include:

- URL
- Whether checks passed
- Whether a download was attempted
- Exit code
- Status string
- Optional message
- Redacted command preview

Exit code rules:

- `0` if all requested operations succeed
- Non-zero if validation fails before downloads
- Non-zero if any batch item fails

## Redaction

Sensitive values must be redacted from:

- Printed URLs
- Header values when they contain credentials or bearer tokens
- Proxy URLs with embedded credentials
- Command previews and log messages

## Modules

- `safetch/cli.py`
- `safetch/config.py`
- `safetch/vpncheck.py`
- `safetch/wget_runner.py`
- `safetch/input_file.py`
- `safetch/redact.py`
- `safetch/result.py`
- `safetch/__main__.py`
