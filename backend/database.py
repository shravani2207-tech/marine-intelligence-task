from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def connect(database_path: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(database_path, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'analyst', 'viewer')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL
            )
            """
        )


def get_user_by_email(database_path: Path, email: str) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT id, email, password_hash, role, is_active, created_at "
            "FROM users WHERE email = ?",
            (email,),
        ).fetchone()


def get_user_by_id(database_path: Path, user_id: str) -> sqlite3.Row | None:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT id, email, password_hash, role, is_active, created_at "
            "FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()


def list_users(database_path: Path) -> list[sqlite3.Row]:
    with connect(database_path) as connection:
        return connection.execute(
            "SELECT id, email, role, is_active, created_at FROM users ORDER BY email"
        ).fetchall()
