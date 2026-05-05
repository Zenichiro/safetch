from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class DownloadResult:
    url: str
    ok: bool
    checks_passed: bool
    attempted_download: bool
    exit_code: int
    status: str
    message: str | None = None
    command_preview: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
