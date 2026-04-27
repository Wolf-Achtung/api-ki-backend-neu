# -*- coding: utf-8 -*-
"""Tests for the Step 5 auth-helpers in core.security.

Schwerpunkt: das Feature-Flag STEP5_JWT_ENFORCEMENT muss live umflippbar
sein, ohne Re-Deploy. Tests laufen mit/ohne Flag und decken die fünf
Pfade durch ``step5_principal`` ab.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException


# --- step5_jwt_enforcement_enabled --------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        ("1", True),
        ("true", True),
        ("True", True),
        ("yes", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("", False),
        ("garbage", False),
    ],
)
def test_step5_flag_parsing(value: str, expected: bool) -> None:
    from core.security import step5_jwt_enforcement_enabled
    with patch.dict(os.environ, {"STEP5_JWT_ENFORCEMENT": value}):
        assert step5_jwt_enforcement_enabled() is expected


def test_step5_flag_unset_is_false() -> None:
    from core.security import step5_jwt_enforcement_enabled
    env = dict(os.environ)
    env.pop("STEP5_JWT_ENFORCEMENT", None)
    with patch.dict(os.environ, env, clear=True):
        assert step5_jwt_enforcement_enabled() is False


# --- step5_principal: Flag OFF (legacy passthrough) --------------------


def _no_flag_env() -> dict:
    env = dict(os.environ)
    env.pop("STEP5_JWT_ENFORCEMENT", None)
    return env


def test_principal_flag_off_no_token_returns_unauthenticated() -> None:
    from core.security import step5_principal
    with patch.dict(os.environ, _no_flag_env(), clear=True):
        result = step5_principal(auth_token=None, authorization=None, x_service_token=None)
    assert result.is_authenticated is False
    assert result.is_service is False
    assert result.email is None
    assert result.identity == "anonymous"


def test_principal_flag_off_invalid_token_swallowed() -> None:
    """Mit Flag aus: ungültiges Token darf das Verhalten nicht brechen."""
    from core.security import step5_principal
    with patch.dict(os.environ, _no_flag_env(), clear=True):
        result = step5_principal(
            auth_token="not-a-real-jwt", authorization=None, x_service_token=None,
        )
    assert result.is_authenticated is False


# --- step5_principal: Flag ON ------------------------------------------


def _flag_on_env() -> dict:
    env = dict(os.environ)
    env["STEP5_JWT_ENFORCEMENT"] = "1"
    return env


def test_principal_flag_on_no_token_raises_401() -> None:
    from core.security import step5_principal
    with patch.dict(os.environ, _flag_on_env(), clear=True):
        with pytest.raises(HTTPException) as exc:
            step5_principal(auth_token=None, authorization=None, x_service_token=None)
    assert exc.value.status_code == 401


def test_principal_flag_on_invalid_jwt_raises() -> None:
    """Ungültiges JWT mit Flag on → 401 (nicht stillschweigend durchwinken)."""
    from core.security import step5_principal
    with patch.dict(os.environ, _flag_on_env(), clear=True):
        with pytest.raises(HTTPException):
            step5_principal(
                auth_token="garbage", authorization=None, x_service_token=None,
            )


def test_principal_flag_on_valid_jwt_whitelisted_email_passes() -> None:
    """Echter Round-Trip: erzeuge Token, dekodiere ihn — whitelisted email akzeptiert."""
    from core.security import create_access_token, step5_principal
    from core.whitelist import EMAIL_WHITELIST

    # Pick an email that is in the canonical whitelist
    email = next(iter(EMAIL_WHITELIST))
    token = create_access_token(email=email)
    with patch.dict(os.environ, _flag_on_env(), clear=True):
        result = step5_principal(
            auth_token=token, authorization=None, x_service_token=None,
        )
    assert result.is_authenticated is True
    assert result.is_service is False
    assert result.email == email


def test_principal_flag_on_valid_jwt_non_whitelisted_email_403() -> None:
    """JWT für nicht-whitelisted Email → 403, nicht 200."""
    from core.security import create_access_token, step5_principal

    token = create_access_token(email="random@stranger.tld")
    with patch.dict(os.environ, _flag_on_env(), clear=True):
        with pytest.raises(HTTPException) as exc:
            step5_principal(
                auth_token=token, authorization=None, x_service_token=None,
            )
    assert exc.value.status_code == 403


# --- resolve_pipeline_email --------------------------------------------


def test_resolve_email_service_token_passes_body_email_through() -> None:
    """Service-Tokens dürfen body_email frei setzen (Golden-Reports-Fall)."""
    from core.security import AuthenticatedPrincipal, resolve_pipeline_email
    p = AuthenticatedPrincipal(
        service_principal="golden_reports", is_service=True, is_authenticated=True,
    )
    assert resolve_pipeline_email(p, "anywhere@example.com") == "anywhere@example.com"
    assert resolve_pipeline_email(p, None) is None


def test_resolve_email_user_token_match_returns_token_email() -> None:
    from core.security import AuthenticatedPrincipal, resolve_pipeline_email
    p = AuthenticatedPrincipal(email="user@a.tld", is_authenticated=True)
    # Match — token email returned regardless of body
    assert resolve_pipeline_email(p, "user@a.tld") == "user@a.tld"
    # Case-insensitive
    assert resolve_pipeline_email(p, "USER@A.TLD") == "user@a.tld"
    # No body email — token email returned
    assert resolve_pipeline_email(p, None) == "user@a.tld"


def test_resolve_email_user_token_mismatch_raises_403() -> None:
    from core.security import AuthenticatedPrincipal, resolve_pipeline_email
    p = AuthenticatedPrincipal(email="user@a.tld", is_authenticated=True)
    with pytest.raises(HTTPException) as exc:
        resolve_pipeline_email(p, "attacker@evil.tld")
    assert exc.value.status_code == 403


def test_resolve_email_unauthenticated_passes_body_through() -> None:
    """Flag off + kein Token: legacy passthrough."""
    from core.security import AuthenticatedPrincipal, resolve_pipeline_email
    p = AuthenticatedPrincipal(is_authenticated=False)
    assert resolve_pipeline_email(p, "x@y.tld") == "x@y.tld"
    assert resolve_pipeline_email(p, None) is None


# --- AuthenticatedPrincipal.identity ------------------------------------


def test_identity_service() -> None:
    from core.security import AuthenticatedPrincipal
    p = AuthenticatedPrincipal(
        service_principal="ci_runner", is_service=True, is_authenticated=True,
    )
    assert p.identity == "service:ci_runner"


def test_identity_user() -> None:
    from core.security import AuthenticatedPrincipal
    p = AuthenticatedPrincipal(email="x@y.tld", is_authenticated=True)
    assert p.identity == "user:x@y.tld"


def test_identity_anonymous() -> None:
    from core.security import AuthenticatedPrincipal
    p = AuthenticatedPrincipal(is_authenticated=False)
    assert p.identity == "anonymous"
