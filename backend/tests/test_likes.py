"""Tests for like endpoints."""
import pytest


class TestToggleLike:
    async def test_like_post(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        # Like
        resp = await async_client.post("/api/v1/likes", json={
            "target_type": "post", "target_id": pid
        }, headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["liked"] is True
        assert data["data"]["like_count"] == 1

    async def test_unlike_post(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        # Like then unlike (toggle)
        await async_client.post("/api/v1/likes", json={
            "target_type": "post", "target_id": pid
        }, headers=auth_headers)
        resp = await async_client.post("/api/v1/likes", json={
            "target_type": "post", "target_id": pid
        }, headers=auth_headers)
        data = resp.json()
        assert data["data"]["liked"] is False
        assert data["data"]["like_count"] == 0

    async def test_like_comment(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]
        c_resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Comment"
        }, headers=auth_headers)
        cid = c_resp.json()["data"]["id"]

        resp = await async_client.post("/api/v1/likes", json={
            "target_type": "comment", "target_id": cid
        }, headers=auth_headers)
        data = resp.json()
        assert data["data"]["liked"] is True
        assert data["data"]["like_count"] == 1


class TestLikeStatus:
    async def test_status_before_like(self, async_client, auth_headers):
        resp = await async_client.get("/api/v1/likes/status", params={
            "target_type": "post", "target_id": 1
        }, headers=auth_headers)
        assert resp.json()["data"]["liked"] is False

    async def test_status_after_like(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        await async_client.post("/api/v1/likes", json={
            "target_type": "post", "target_id": pid
        }, headers=auth_headers)

        resp = await async_client.get("/api/v1/likes/status", params={
            "target_type": "post", "target_id": pid
        }, headers=auth_headers)
        assert resp.json()["data"]["liked"] is True
