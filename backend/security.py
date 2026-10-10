from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt import InvalidTokenError


PASSWORD_ITERATIONS = 600_000
ACCESS_TOKEN_MINUTES = 30
TOKEN_ISSUER = "marine-intelligence-api"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(derived_key).decode("ascii"),
    )


DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, iterations, salt_text, expected_text = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(expected_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def get_signing_key(configured_key: str | None = None) -> str:
    key = configured_key or os.getenv("AUTH_SECRET_KEY")
    if not key or len(key.encode("utf-8")) < 32:
        raise RuntimeError(
            "AUTH_SECRET_KEY must be set to a secret of at least 32 bytes."
        )
    return key


def create_access_token(user_id: str, signing_key: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
            "iss": TOKEN_ISSUER,
            "jti": str(uuid4()),
        },
        get_signing_key(signing_key),
        algorithm="HS256",
    )


def decode_access_token(
    token: str, signing_key: str | None = None
) -> dict[str, object]:
    return jwt.decode(
        token,
        get_signing_key(signing_key),
        algorithms=["HS256"],
        issuer=TOKEN_ISSUER,
        options={"require": ["sub", "iat", "exp", "iss", "jti"]},
    )


class TokenError(Exception):
    pass


def token_subject(token: str, signing_key: str | None = None) -> str:
    try:
        claims = decode_access_token(token, signing_key)
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise TokenError("Token has no valid subject.")
        return subject
    except InvalidTokenError as exc:
        raise TokenError("Token is invalid or expired.") from exc
