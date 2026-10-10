from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.config import PROJECT_ROOT
from backend.database import (
    connect,
    get_user_by_email,
    get_user_by_id,
    initialize_database,
    list_users,
)
from backend.security import (
    ACCESS_TOKEN_MINUTES,
    DUMMY_PASSWORD_HASH,
    TokenError,
    create_access_token,
    hash_password,
    get_signing_key,
    token_subject,
    verify_password,
)


logger = logging.getLogger(__name__)
DATASETS = {
    "ports": PROJECT_ROOT / "ports.json",
    "waterways": PROJECT_ROOT / "waterways.json",
    "coastal_zones": PROJECT_ROOT / "coastal_zones.json",
    "environmental": PROJECT_ROOT / "environmental.json",
    "logistics": PROJECT_ROOT / "logistics.json",
}
ASSESSMENTS = {
    "feasibility": PROJECT_ROOT / "mmr_feasibility_report.json",
    "financial": PROJECT_ROOT / "mmr_financial_report.json",
    "scenario_simulation": PROJECT_ROOT / "mmr_scenario_simulation_report.json",
    "intelligence": PROJECT_ROOT / "mmr_intelligence_result.json",
}
Role = Literal["admin", "analyst", "viewer"]
bearer_scheme = HTTPBearer(auto_error=False)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Credentials(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().casefold()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("A valid email address is required.")
        return value


class UserResponse(BaseModel):
    id: str
    email: str
    role: Role
    is_active: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse


class RoleUpdate(StrictModel):
    role: Role


class ActiveUpdate(StrictModel):
    is_active: bool


def public_user(row: sqlite3.Row) -> UserResponse:
    return UserResponse(
        id=row["id"],
        email=row["email"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


def database_path_for(request: Request) -> Path:
    return request.app.state.database_path


def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Security(bearer_scheme)
    ],
) -> UserResponse:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = token_subject(
            credentials.credentials, request.app.state.signing_key
        )
    except (TokenError, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    row = get_user_by_id(database_path_for(request), user_id)
    if row is None or not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return public_user(row)


def require_roles(*allowed_roles: str):
    def role_guard(
        current_user: Annotated[UserResponse, Depends(get_current_user)],
    ) -> UserResponse:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role does not have permission to perform this action.",
            )
        return current_user

    return role_guard


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_signing_key(app.state.signing_key)
    initialize_database(app.state.database_path)
    yield


def create_app(
    database_path: str | Path | None = None, signing_key: str | None = None
) -> FastAPI:
    app = FastAPI(
        title="Marine Intelligence API",
        version="1.0.0",
        lifespan=lifespan,
    )
    configured_path = database_path or os.getenv(
        "DATABASE_PATH"
    ) or str(PROJECT_ROOT / "marine_intelligence.db")
    app.state.database_path = Path(configured_path).resolve()
    app.state.signing_key = signing_key

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/auth/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def register(
        credentials: Credentials, request: Request
    ) -> UserResponse:
        database_path = database_path_for(request)
        user_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            with connect(database_path) as connection:
                connection.execute(
                    "INSERT INTO users (id, email, password_hash, role, created_at) "
                    "VALUES (?, ?, ?, 'viewer', ?)",
                    (
                        user_id,
                        credentials.email,
                        hash_password(credentials.password),
                        now,
                    ),
                )
                row = connection.execute(
                    "SELECT id, email, role, is_active, created_at "
                    "FROM users WHERE id = ?",
                    (user_id,),
                ).fetchone()
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from None
        return public_user(row)

    @app.post("/auth/login", response_model=TokenResponse)
    def login(credentials: Credentials, request: Request) -> TokenResponse:
        row = get_user_by_email(database_path_for(request), credentials.email)
        password_hash = (
            row["password_hash"] if row is not None else DUMMY_PASSWORD_HASH
        )
        password_matches = verify_password(credentials.password, password_hash)
        if (
            row is None
            or not row["is_active"]
            or not password_matches
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email or password is incorrect.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = public_user(row)
        token = create_access_token(user.id, request.app.state.signing_key)
        return TokenResponse(
            access_token=token,
            expires_in=ACCESS_TOKEN_MINUTES * 60,
            user=user,
        )

    @app.get("/auth/me", response_model=UserResponse)
    def current_user(
        user: Annotated[UserResponse, Depends(get_current_user)],
    ) -> UserResponse:
        return user

    @app.get("/api/datasets/{dataset_name}")
    def read_dataset(
        dataset_name: str,
        _user: Annotated[UserResponse, Depends(get_current_user)],
    ):
        path = DATASETS.get(dataset_name)
        if path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found."
            )
        try:
            with path.open("r", encoding="utf-8") as dataset_file:
                return json.load(dataset_file)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset is not available.",
            ) from None
        except json.JSONDecodeError:
            logger.exception("Configured dataset %s contains invalid JSON.", dataset_name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dataset could not be read.",
            ) from None

    @app.get("/api/assessments/{assessment_name}")
    def read_assessment(
        assessment_name: str,
        _user: Annotated[
            UserResponse, Depends(require_roles("admin", "analyst"))
        ],
    ):
        path = ASSESSMENTS.get(assessment_name)
        if path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found.",
            )
        try:
            with path.open("r", encoding="utf-8") as assessment_file:
                return json.load(assessment_file)
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment is not available.",
            ) from None
        except json.JSONDecodeError:
            logger.exception(
                "Configured assessment %s contains invalid JSON.", assessment_name
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Assessment could not be read.",
            ) from None

    @app.get("/admin/users", response_model=list[UserResponse])
    def get_users(
        _admin: Annotated[UserResponse, Depends(require_roles("admin"))],
        request: Request,
    ) -> list[UserResponse]:
        return [public_user(row) for row in list_users(database_path_for(request))]

    @app.patch("/admin/users/{user_id}/role", response_model=UserResponse)
    def change_user_role(
        user_id: str,
        update: RoleUpdate,
        request: Request,
        _admin: Annotated[UserResponse, Depends(require_roles("admin"))],
    ) -> UserResponse:
        with connect(database_path_for(request)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            target = connection.execute(
                "SELECT id, email, role, is_active, created_at "
                "FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if target is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
                )
            if (
                target["role"] == "admin"
                and target["is_active"]
                and update.role != "admin"
            ):
                active_admins = connection.execute(
                    "SELECT COUNT(*) FROM users "
                    "WHERE role = 'admin' AND is_active = 1"
                ).fetchone()[0]
                if active_admins <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="The last active administrator cannot be demoted.",
                    )
            connection.execute(
                "UPDATE users SET role = ? WHERE id = ?", (update.role, user_id)
            )
            updated = connection.execute(
                "SELECT id, email, role, is_active, created_at "
                "FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return public_user(updated)

    @app.patch("/admin/users/{user_id}/active", response_model=UserResponse)
    def change_user_status(
        user_id: str,
        update: ActiveUpdate,
        request: Request,
        admin: Annotated[UserResponse, Depends(require_roles("admin"))],
    ) -> UserResponse:
        with connect(database_path_for(request)) as connection:
            connection.execute("BEGIN IMMEDIATE")
            target = connection.execute(
                "SELECT id, email, role, is_active, created_at "
                "FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if target is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
                )
            if not update.is_active and target["id"] == admin.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Administrators cannot deactivate their own account.",
                )
            if (
                not update.is_active
                and target["role"] == "admin"
                and target["is_active"]
            ):
                active_admins = connection.execute(
                    "SELECT COUNT(*) FROM users "
                    "WHERE role = 'admin' AND is_active = 1"
                ).fetchone()[0]
                if active_admins <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="The last active administrator cannot be deactivated.",
                    )
            connection.execute(
                "UPDATE users SET is_active = ? WHERE id = ?",
                (int(update.is_active), user_id),
            )
            updated = connection.execute(
                "SELECT id, email, role, is_active, created_at "
                "FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return public_user(updated)

    return app


app = create_app()
