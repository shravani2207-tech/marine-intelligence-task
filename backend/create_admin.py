from __future__ import annotations

import getpass
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from backend.config import PROJECT_ROOT
from backend.database import connect, initialize_database
from backend.security import hash_password


def main() -> None:
    database_path = Path(
        os.getenv("DATABASE_PATH") or PROJECT_ROOT / "marine_intelligence.db"
    ).resolve()
    email = input("Administrator email: ").strip().casefold()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise SystemExit("Enter a valid email address.")

    password = getpass.getpass("Administrator password (12-128 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    if not 12 <= len(password) <= 128:
        raise SystemExit("Password must be between 12 and 128 characters.")

    initialize_database(database_path)
    try:
        with connect(database_path) as connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, role, created_at) "
                "VALUES (?, ?, ?, 'admin', ?)",
                (
                    str(uuid4()),
                    email,
                    hash_password(password),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
    except sqlite3.IntegrityError:
        raise SystemExit("An account with this email already exists.") from None
    print(f"Administrator created in {database_path}.")


if __name__ == "__main__":
    main()
