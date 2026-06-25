"""Tests for post endpoints."""
import pytest


class TestCreatePost:
    async def test_create_success(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "Test Post", "content": "Hello world!", "summary": "test"
        }, headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["title"] == "Test Post"
        assert data["data"]["content"] == "Hello world!"
        assert data["data"]["author_id"] == 1
        assert data["data"]["status"] == "published"

    async def test_create_unauthenticated(self, async_client):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "No Auth", "content": "fail"
        })
        assert resp.status_code in (401, 403)

    async def test_create_with_draft_status(self, async_client, auth_headers):
        resp = await async_client.post("/api/v1/posts", json={
            "title": "Draft Post", "content": "draft content", "status": "draft"
        }, headers=auth_headers)
        assert resp.json()["data"]["status"] == "draft"


class TestListPosts:
    async def test_list_published(self, async_client, auth_headers):
        await async_client.post("/api/v1/posts", json={
            "title": "P1", "content": "c1"
        }, headers=auth_headers)
        resp = await async_client.get("/api/v1/posts")
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 1
        assert len(data["data"]["items"]) == 1

    async def test_list_excludes_drafts(self, async_client, auth_headers):
        await async_client.post("/api/v1/posts", json={
            "title": "Draft", "content": "d", "status": "draft"
        }, headers=auth_headers)
        resp = await async_client.get("/api/v1/posts")
        assert resp.json()["data"]["total"] == 0

    async def test_list_search(self, async_client, auth_headers):
        await async_client.post("/api/v1/posts", json={
            "title": "Python Tips", "content": "Learn Python",
        }, headers=auth_headers)
        await async_client.post("/api/v1/posts", json={
            "title": "JavaScript Guide", "content": "Learn JS",
        }, headers=auth_headers)
        resp = await async_client.get("/api/v1/posts", params={"q": "Python"})
        data = resp.json()
        assert data["data"]["total"] == 1
        assert data["data"]["items"][0]["title"] == "Python Tips"


class TestGetPost:
    async def test_get_and_increment_view(self, async_client, auth_headers):
        create_resp = await async_client.post("/api/v1/posts", json={
            "title": "T", "content": "C"
        }, headers=auth_headers)
        pid = create_resp.json()["data"]["id"]

        resp = await async_client.get(f"/api/v1/posts/{pid}")
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["view_count"] == 1

    async def test_get_not_found(self, async_client):
        resp = await async_client.get("/api/v1/posts/999")
        assert resp.json()["code"] != 0
        assert resp.status_code == 404


class TestUpdatePost:
    async def test_update_as_author(self, async_client, auth_headers):
        create_resp = await async_client.post("/api/v1/posts", json={
            "title": "Old", "content": "old"
        }, headers=auth_headers)
        pid = create_resp.json()["data"]["id"]

        resp = await async_client.put(f"/api/v1/posts/{pid}", json={
            "title": "New Title"
        }, headers=auth_headers)
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["title"] == "New Title"
        assert data["data"]["content"] == "old"  # unchanged

    async def test_update_forbidden(self, async_client, auth_headers, auth_headers2):
        create_resp = await async_client.post("/api/v1/posts", json={
            "title": "Mine", "content": "mine"
        }, headers=auth_headers)
        pid = create_resp.json()["data"]["id"]

        resp = await async_client.put(f"/api/v1/posts/{pid}", json={
            "title": "Hacked"
        }, headers=auth_headers2)
        assert resp.status_code == 403


class TestDeletePost:
    async def test_delete_as_author(self, async_client, auth_headers):
        create_resp = await async_client.post("/api/v1/posts", json={
            "title": "ToDelete", "content": "bye"
        }, headers=auth_headers)
        pid = create_resp.json()["data"]["id"]

        resp = await async_client.delete(f"/api/v1/posts/{pid}", headers=auth_headers)
        assert resp.json()["code"] == 0

        get_resp = await async_client.get(f"/api/v1/posts/{pid}")
        assert get_resp.status_code == 404

    async def test_delete_forbidden(self, async_client, auth_headers, auth_headers2):
        create_resp = await async_client.post("/api/v1/posts", json={
            "title": "Mine", "content": "mine"
        }, headers=auth_headers)
        pid = create_resp.json()["data"]["id"]

        resp = await async_client.delete(f"/api/v1/posts/{pid}", headers=auth_headers2)
        assert resp.status_code == 403
