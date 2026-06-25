"""Tests for comment endpoints."""
import pytest


class TestCreateComment:
    async def test_create_top_level(self, async_client, auth_headers):
        # First create a post
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Nice post!"
        }, headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["content"] == "Nice post!"
        assert data["data"]["parent_id"] is None
        assert data["data"]["replies"] == []

    async def test_create_reply(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        parent_resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Parent"
        }, headers=auth_headers)
        parent_id = parent_resp.json()["data"]["id"]

        resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Reply", "parent_id": parent_id
        }, headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["parent_id"] == parent_id

    async def test_create_unauthenticated(self, async_client):
        resp = await async_client.post("/api/v1/comments?post_id=1", json={
            "content": "No auth"
        })
        assert resp.status_code in (401, 403)

    async def test_post_not_found(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/comments?post_id=999", json={
            "content": "Where?"
        }, headers=auth_headers)
        assert resp.status_code == 404


class TestListComments:
    async def test_threaded_structure(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        # Create parent + reply
        p_resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Parent"
        }, headers=auth_headers)
        parent_id = p_resp.json()["data"]["id"]
        await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Child", "parent_id": parent_id
        }, headers=auth_headers)

        resp = await async_client.get(f"/api/v1/comments/post/{pid}")
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1  # 1 top-level
        assert len(data["data"][0]["replies"]) == 1  # 1 reply nested
        assert data["data"][0]["replies"][0]["content"] == "Child"


class TestUpdateComment:
    async def test_update_as_author(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]
        c_resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Old"
        }, headers=auth_headers)
        cid = c_resp.json()["data"]["id"]

        resp = await async_client.put(f"/api/v1/comments/{cid}", json={
            "content": "Updated"
        }, headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["content"] == "Updated"


class TestDeleteComment:
    async def test_delete_with_cascade_count(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]

        # Create parent + 2 replies
        p_resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Parent"
        }, headers=auth_headers)
        parent_id = p_resp.json()["data"]["id"]
        await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Child1", "parent_id": parent_id
        }, headers=auth_headers)
        await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "Child2", "parent_id": parent_id
        }, headers=auth_headers)

        # Delete parent — should cascade delete 2 replies, comment_count -= 3
        resp = await async_client.delete(f"/api/v1/comments/{parent_id}", headers=auth_headers)
        assert resp.json()["code"] == 0

        # Verify comment count
        post_resp = await async_client.get(f"/api/v1/posts/{pid}")
        assert post_resp.json()["data"]["comment_count"] == 0

    async def test_delete_forbidden(self, async_client, auth_headers, auth_headers2):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "P", "content": "C"
        }, headers=auth_headers)
        pid = resp.json()["data"]["id"]
        c_resp = await async_client.post(f"/api/v1/comments?post_id={pid}", json={
            "content": "mine"
        }, headers=auth_headers)
        cid = c_resp.json()["data"]["id"]

        resp = await async_client.delete(f"/api/v1/comments/{cid}", headers=auth_headers2)
        assert resp.status_code == 403
