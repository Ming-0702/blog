"""Tests for auth endpoints."""
import pytest


class TestRegister:
    async def test_register_success(self, async_client):
        resp = await async_client.post("/api/v1/auth/register", json={
            "username": "newuser", "email": "new@test.com", "password": "pass1234"
        })
        data = resp.json()
        assert resp.status_code == 200
        assert data["code"] == 0
        assert data["data"]["user"]["username"] == "newuser"
        assert "access_token" in data["data"]

    async def test_register_duplicate_username(self, async_client, test_user):
        resp = await async_client.post("/api/v1/auth/register", json={
            "username": "lg鹿铭", "email": "diff@test.com", "password": "pass1234"
        })
        assert resp.json()["code"] != 0

    async def test_register_duplicate_email(self, async_client, test_user):
        resp = await async_client.post("/api/v1/auth/register", json={
            "username": "diffuser", "email": "test@test.com", "password": "pass1234"
        })
        assert resp.json()["code"] != 0


class TestLogin:
    async def test_login_success_username(self, async_client, test_user):
        resp = await async_client.post("/api/v1/auth/login", json={
            "username": "lg鹿铭", "password": "password123"
        })
        data = resp.json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert data["data"]["user"]["username"] == "lg鹿铭"

    async def test_login_success_email(self, async_client, test_user):
        resp = await async_client.post("/api/v1/auth/login", json={
            "username": "test@test.com", "password": "password123"
        })
        assert resp.json()["code"] == 0

    async def test_login_wrong_password(self, async_client, test_user):
        resp = await async_client.post("/api/v1/auth/login", json={
            "username": "lg鹿铭", "password": "wrongpassword"
        })
        assert resp.json()["code"] != 0
        assert resp.status_code == 401


class TestGetMe:
    async def test_get_me_authenticated(self, async_client, auth_headers):
        resp = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["username"] == "lg鹿铭"

    async def test_get_me_unauthenticated(self, async_client):
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)
