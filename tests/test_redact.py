from safetch.redact import redact_header, redact_text, redact_url


def test_redact_url_hides_embedded_credentials() -> None:
    value = "https://user:pass@example.com/file.bin"
    assert redact_url(value) == "https://[REDACTED]@example.com/file.bin"


def test_redact_header_hides_authorization_values() -> None:
    assert redact_header("Authorization: Bearer top-secret") == "Authorization: [REDACTED]"


def test_redact_text_hides_bearer_tokens() -> None:
    text = "Authorization: Bearer abc123"
    assert redact_text(text) == "Authorization: [REDACTED]"
