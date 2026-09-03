from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import threading
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable


ROLES = {"ADMIN", "ASSET_OWNER", "SME_VENDOR"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if len(password) < 8:
        raise ValueError("password must contain at least 8 characters")
    if len(password) > 128:
        raise ValueError("password must contain at most 128 characters")
    salt_value = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt_value, n=16384, r=8, p=1, dklen=32)
    return f"scrypt$16384$8$1${salt_value.hex()}${derived.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$", 5)
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=32
        )
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


class AuthService:
    def __init__(self, path: Path, *, token_hours: int = 12,
                 clock: Callable[[], datetime] = utc_now) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.token_hours = max(1, token_hours)
        self.clock = clock
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=5.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, closing(self._connect()) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL, created_at TEXT NOT NULL)"""
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
            additions = {
                "name": "TEXT NOT NULL DEFAULT 'Aegis User'",
                "role": "TEXT NOT NULL DEFAULT 'ASSET_OWNER'",
                "active": "INTEGER NOT NULL DEFAULT 1",
                "organization": "TEXT",
                "team": "TEXT",
            }
            for name, definition in additions.items():
                if name not in columns:
                    connection.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id))"""
            )

    @staticmethod
    def _public(row: sqlite3.Row) -> dict[str, object]:
        return {
            "user_id": str(row["id"]), "name": row["name"], "email": row["email"],
            "role": row["role"], "active": bool(row["active"]),
            "organization": row["organization"], "team": row["team"],
            "created_at": row["created_at"],
        }

    def user_count(self) -> int:
        with self._lock, closing(self._connect()) as connection:
            return int(connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    def register(self, *, name: str, email: str, password: str, role: str = "ASSET_OWNER",
                 organization: str | None = None, team: str | None = None) -> dict[str, object]:
        normalized = email.strip().lower()
        clean_name = name.strip()
        normalized_role = role.strip().upper()
        if not clean_name:
            raise ValueError("name is required")
        if "@" not in normalized or len(normalized) > 254:
            raise ValueError("a valid email is required")
        if normalized_role not in ROLES:
            raise ValueError("role must be ADMIN, ASSET_OWNER, or SME_VENDOR")
        password_hash = hash_password(password)
        now = self.clock().astimezone(timezone.utc).isoformat()
        try:
            with self._lock, closing(self._connect()) as connection:
                cursor = connection.execute(
                    "INSERT INTO users(email,password_hash,created_at,name,role,active,organization,team) VALUES(?,?,?,?,?,1,?,?)",
                    (normalized, password_hash, now, clean_name, normalized_role, organization, team),
                )
                row = connection.execute("SELECT * FROM users WHERE id=?", (cursor.lastrowid,)).fetchone()
        except sqlite3.IntegrityError as exc:
            raise ValueError("email is already registered") from exc
        return self._public(row)

    def authenticate(self, email: str, password: str) -> dict[str, object] | None:
        with self._lock, closing(self._connect()) as connection:
            row = connection.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        if row is None or not bool(row["active"]) or not verify_password(password, row["password_hash"]):
            return None
        return self._public(row)

    def login(self, email: str, password: str) -> dict[str, object]:
        user = self.authenticate(email, password)
        if user is None:
            raise PermissionError("invalid email/password or inactive user")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = self.clock().astimezone(timezone.utc)
        expires = now + timedelta(hours=self.token_hours)
        with self._lock, closing(self._connect()) as connection:
            connection.execute(
                "INSERT INTO auth_sessions VALUES(?,?,?,?,NULL)",
                (token_hash, int(str(user["user_id"])), now.isoformat(), expires.isoformat()),
            )
        return {
            "access_token": token, "token_type": "bearer",
            "expires_at": expires.isoformat(), "user": user,
        }

    def current_user(self, token: str) -> dict[str, object] | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = self.clock().astimezone(timezone.utc)
        with self._lock, closing(self._connect()) as connection:
            row = connection.execute(
                """SELECT users.* FROM auth_sessions JOIN users ON users.id=auth_sessions.user_id
                WHERE token_hash=? AND revoked_at IS NULL AND expires_at>? AND users.active=1""",
                (token_hash, now.isoformat()),
            ).fetchone()
        return self._public(row) if row else None

    def logout(self, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self._lock, closing(self._connect()) as connection:
            cursor = connection.execute(
                "UPDATE auth_sessions SET revoked_at=? WHERE token_hash=? AND revoked_at IS NULL",
                (self.clock().astimezone(timezone.utc).isoformat(), token_hash),
            )
        return cursor.rowcount > 0

    def list_users(self) -> list[dict[str, object]]:
        with self._lock, closing(self._connect()) as connection:
            rows = connection.execute("SELECT * FROM users ORDER BY name,email").fetchall()
        return [self._public(row) for row in rows]

    def get_user(self, user_id: str) -> dict[str, object] | None:
        with self._lock, closing(self._connect()) as connection:
            row = connection.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return self._public(row) if row else None

    def set_active(self, user_id: str, active: bool) -> None:
        with self._lock, closing(self._connect()) as connection:
            connection.execute("UPDATE users SET active=? WHERE id=?", (int(active), user_id))
