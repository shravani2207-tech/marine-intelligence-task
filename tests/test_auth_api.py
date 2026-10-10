from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.database import connect, initialize_database
from backend.main import create_app
from backend.security import hash_password


class AuthApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_directory.name) / "test.db"
        self.signing_key = "test-only-signing-key-with-32-bytes-min"
        self.app = create_app(self.database_path, self.signing_key)
        self.client = TestClient(self.app)
        self.client.__enter__()
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self.temp_directory.cleanup()

    def register(self, email: str = "viewer@example.org") -> dict:
        response = self.client.post(
            "/auth/register",
            json={"email": email, "password": "long-enough-test-password"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def add_user(self, email: str, role: str) -> dict:
        from datetime import datetime, timezone
        from uuid import uuid4

        user_id = str(uuid4())
        with connect(self.database_path) as connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, role, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    email,
                    hash_password("long-enough-test-password"),
                    role,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        return {"id": user_id, "email": email, "role": role}

    def test_registration_creates_viewer_and_rejects_role_escalation(self) -> None:
        response = self.client.post(
            "/auth/register",
            json={
                "email": "user@example.org",
                "password": "long-enough-test-password",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 422)

        user = self.register("USER@example.org")
        self.assertEqual(user["role"], "viewer")
        self.assertEqual(user["email"], "user@example.org")
        self.assertNotIn("password_hash", user)
        duplicate = self.client.post(
            "/auth/register",
            json={
                "email": "user@example.org",
                "password": "long-enough-test-password",
            },
        )
        self.assertEqual(duplicate.status_code, 409)

    def test_login_and_current_user_require_valid_credentials(self) -> None:
        user = self.register()
        login = self.client.post(
            "/auth/login",
            json={
                "email": "viewer@example.org",
                "password": "long-enough-test-password",
            },
        )
        self.assertEqual(login.status_code, 200, login.text)
        token = login.json()["access_token"]
        self.assertEqual(login.json()["user"]["id"], user["id"])

        current = self.client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(current.status_code, 200)
        self.assertEqual(current.json()["role"], "viewer")
        self.assertEqual(self.client.get("/auth/me").status_code, 401)

        invalid = self.client.post(
            "/auth/login",
            json={"email": "viewer@example.org", "password": "wrong-password"},
        )
        self.assertEqual(invalid.status_code, 401)

    def test_role_permissions_separate_viewer_analyst_and_admin(self) -> None:
        viewer = self.register()
        analyst = self.add_user("analyst@example.org", "analyst")
        admin = self.add_user("admin@example.org", "admin")

        def token_for(email: str) -> str:
            response = self.client.post(
                "/auth/login",
                json={"email": email, "password": "long-enough-test-password"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()["access_token"]

        viewer_headers = {"Authorization": f"Bearer {token_for(viewer['email'])}"}
        analyst_headers = {"Authorization": f"Bearer {token_for(analyst['email'])}"}
        admin_headers = {"Authorization": f"Bearer {token_for(admin['email'])}"}

        self.assertEqual(
            self.client.get("/api/datasets/ports", headers=viewer_headers).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                "/api/assessments/feasibility", headers=viewer_headers
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                "/api/assessments/feasibility", headers=analyst_headers
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/admin/users", headers=analyst_headers).status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/admin/users", headers=admin_headers).status_code,
            200,
        )

    def test_admin_management_prevents_lockout_and_disables_tokens(self) -> None:
        admin = self.add_user("admin@example.org", "admin")
        viewer = self.register()
        login = self.client.post(
            "/auth/login",
            json={
                "email": "admin@example.org",
                "password": "long-enough-test-password",
            },
        )
        viewer_login = self.client.post(
            "/auth/login",
            json={
                "email": "viewer@example.org",
                "password": "long-enough-test-password",
            },
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        viewer_headers = {
            "Authorization": f"Bearer {viewer_login.json()['access_token']}"
        }

        demote_last_admin = self.client.patch(
            f"/admin/users/{admin['id']}/role",
            json={"role": "viewer"},
            headers=headers,
        )
        self.assertEqual(demote_last_admin.status_code, 409)
        deactivate_self = self.client.patch(
            f"/admin/users/{admin['id']}/active",
            json={"is_active": False},
            headers=headers,
        )
        self.assertEqual(deactivate_self.status_code, 409)

        promoted = self.client.patch(
            f"/admin/users/{viewer['id']}/role",
            json={"role": "analyst"},
            headers=headers,
        )
        self.assertEqual(promoted.status_code, 200)
        self.assertEqual(promoted.json()["role"], "analyst")

        self.assertEqual(
            self.client.patch(
                f"/admin/users/{viewer['id']}/active",
                json={"is_active": False},
                headers=headers,
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get("/auth/me", headers=viewer_headers).status_code,
            401,
        )


if __name__ == "__main__":
    unittest.main()
