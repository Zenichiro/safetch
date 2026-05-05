from pathlib import Path

from safetch.input_file import parse_input_file


def test_parse_input_file_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    source = tmp_path / "urls.txt"
    source.write_text(
        "\n# comment\nhttps://example.com/file.bin\n  \nhttps://example.org/archive.zip\n",
        encoding="utf-8",
    )

    assert parse_input_file(source) == [
        "https://example.com/file.bin",
        "https://example.org/archive.zip",
    ]
