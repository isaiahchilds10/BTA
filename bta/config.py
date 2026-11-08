"""Configuration loader. Never commit credentials or print their values."""
from __future__ import annotations
import os


def setting(key: str, default: str = "") -> str:
    if os.environ.get(key):
        return os.environ[key]
    try:
        import streamlit as st
        return str(st.secrets.get(key, default))
    except (ImportError, FileNotFoundError, KeyError):
        return default


def mode() -> str:
    value = setting("BTA_MODE", "private").lower()
    if value not in {"demo", "private"}:
        raise ValueError("BTA_MODE must be demo or private")
    return value


def auth_ready() -> bool:
    return bool(setting("SUPABASE_URL") and (setting("SUPABASE_SECRET_KEY") or setting("SUPABASE_SERVICE_ROLE_KEY")))


def admin_ready() -> bool:
    return auth_ready() and bool(setting("SUPABASE_SERVICE_ROLE_KEY"))
