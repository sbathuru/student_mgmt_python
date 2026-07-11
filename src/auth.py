"""Simple authentication utilities: in-memory user store, registration,
login and JWT token helpers used by the Flask app.

This is intentionally lightweight for demonstration; in production use a
proper user database and secure password policies.
"""
import os
import time
from typing import Optional

import jwt
from passlib.hash import bcrypt
from flask import current_app

from .oracle_user_db import OracleUserStore


class User:
    def __init__(self, user_id: int, email: str, password_hash: str):
        self.id = user_id
        self.email = email
        self.password_hash = password_hash


# Prefer Oracle user store when Oracle env vars are present and oracledb available
def _choose_user_store():
    # Enforce Oracle-only storage. This will raise at startup if Oracle is
    # not configured or the `oracledb` package is not available.
    if not (os.getenv("ORACLE_USER") and os.getenv("ORACLE_PASSWORD") and os.getenv("ORACLE_DSN")):
        raise RuntimeError("Oracle configuration required: set ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN")
    return OracleUserStore()


USER_STORE = _choose_user_store()


def register_user(email: str, password: str) -> dict:
    if not email or not password:
        raise ValueError("Email and password are required")
    pw_hash = bcrypt.hash(password)
    user = USER_STORE.add_user(email, pw_hash)
    return {"id": user.id, "email": user.email}


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = USER_STORE.find_by_email(email)
    if user is None:
        return None
    if not bcrypt.verify(password, user.password_hash):
        return None
    # create JWT
    secret = current_app.config.get("SECRET_KEY") or current_app.secret_key
    payload = {
        "sub": user.id,
        "email": user.email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60 * 60 * 24,  # 24h
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"token": token, "user": {"id": user.id, "email": user.email}}


def verify_token(token: str) -> Optional[dict]:
    secret = current_app.config.get("SECRET_KEY") or current_app.secret_key
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except Exception:
        return None
