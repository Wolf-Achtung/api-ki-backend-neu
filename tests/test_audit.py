import pytest

from core.audit import anonymize_ip


def test_anonymize_ipv4_default():
    assert anonymize_ip("203.0.113.42") == "203.0.113.0"


def test_anonymize_ipv4_already_zeroed():
    assert anonymize_ip("10.0.0.0") == "10.0.0.0"


def test_anonymize_ipv6_default():
    assert anonymize_ip("2001:db8:1234:5678::1") == "2001:db8:1234::"


def test_full_ip_when_flag_set(monkeypatch):
    monkeypatch.setenv("AUDIT_FULL_IP", "1")
    assert anonymize_ip("203.0.113.42") == "203.0.113.42"


def test_full_ip_flag_zero_still_anonymizes(monkeypatch):
    monkeypatch.setenv("AUDIT_FULL_IP", "0")
    assert anonymize_ip("203.0.113.42") == "203.0.113.0"


def test_invalid_ip_passthrough():
    assert anonymize_ip("not-an-ip") == "not-an-ip"


def test_none_passthrough():
    assert anonymize_ip(None) is None


def test_empty_string_passthrough():
    assert anonymize_ip("") == ""
