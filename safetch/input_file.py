from __future__ import annotations

from pathlib import Path


def parse_input_file(path: str | Path) -> list[str]:
    file_path = Path(path).expanduser()
    urls: list[str] = []

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)

    return urls
