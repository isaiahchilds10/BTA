"""Validation of a Streamlit-verified Google OpenID Connect identity.

Streamlit validates the OIDC signature, expiry, nonce and issuer; this module
validates the expected account fields and never accepts self-reported emails
from app inputs. A Google identity is NOT authorization: the server-side
membership database must separately permit the subject.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str


def validate_google_claims(claims: dict) -> GoogleIdentity:
    if not isinstance(claims, dict):
        raise PermissionError("Google authentication is required")
    subject = str(claims.get("sub") or "")
    email = str(claims.get("email") or "").strip().lower()
    verified = claims.get("email_verified")
    issuer = str(claims.get("iss") or "")
    if issuer and issuer not in ("accounts.google.com", "https://accounts.google.com"):
        raise PermissionError("Unexpected identity provider")
    if verified not in (True, "true", "True") or not _EMAIL.fullmatch(email):
        raise PermissionError("Google has not verified this email address")
    if not subject or len(subject) > 255 or not re.fullmatch(r"[A-Za-z0-9_:\-]+", subject):
        raise PermissionError("Missing stable Google account identity")
    return GoogleIdentity(subject=subject, email=email)
