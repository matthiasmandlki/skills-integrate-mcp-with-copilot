import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

from fastapi import Header, HTTPException


CREDENTIALS_FILE = Path(
    os.environ.get("TEACHER_CREDENTIALS_FILE", Path(__file__).with_name("teachers.json"))
)
PASSWORD_HASH_ITERATIONS = 310_000
SESSION_TTL_SECONDS = 8 * 60 * 60
_sessions = {}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iteration_text, salt_text, digest_text = password_hash.split("$", 3)
        iterations = int(iteration_text)
        if algorithm != "pbkdf2_sha256" or not 100_000 <= iterations <= 1_000_000:
            return False

        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def verify_teacher_credentials(username: str, password: str) -> bool:
    try:
        with CREDENTIALS_FILE.open(encoding="utf-8") as credentials_file:
            teachers = json.load(credentials_file)["teachers"]
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(status_code=503, detail="Teacher login is not configured")

    for teacher in teachers:
        if not isinstance(teacher, dict):
            continue
        configured_username = teacher.get("username")
        password_hash = teacher.get("password_hash")
        if (
            isinstance(configured_username, str)
            and isinstance(password_hash, str)
            and hmac.compare_digest(configured_username, username)
            and verify_password(password, password_hash)
        ):
            return True
    return False


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = (username, time.time() + SESSION_TTL_SECONDS)
    return token


def require_teacher(authorization: str | None = Header(default=None)) -> str:
    scheme, separator, token = (authorization or "").partition(" ")
    session = _sessions.get(token)
    if scheme.lower() != "bearer" or not separator or session is None:
        raise HTTPException(
            status_code=401,
            detail="Teacher login required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, expires_at = session
    if expires_at <= time.time():
        _sessions.pop(token, None)
        raise HTTPException(
            status_code=401,
            detail="Teacher session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def revoke_session(token: str) -> None:
    _sessions.pop(token, None)