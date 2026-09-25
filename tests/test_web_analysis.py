from __future__ import annotations

import pytest

from my_taste.web_analysis import _validate_public_http_url


def test_website_analysis_rejects_non_http():
    with pytest.raises(ValueError):
        _validate_public_http_url("file:///etc/passwd")


def test_website_analysis_rejects_localhost():
    with pytest.raises(ValueError):
        _validate_public_http_url("http://127.0.0.1:8080")
