"""
Banquoite — Chat API Tests

Tests:
  - Chatroom CRUD (create, list)
  - Message history retrieval
  - Access control (user isolation)
  - SSE streaming endpoint
"""

import pytest
from httpx import AsyncClient

from backend.db.models import Chatroom, Message, User
from backend.tests.conftest import auth_headers


@pytest.mark.asyncio
class TestChatroomCRUD:
    """Tests for chatroom creation and listing."""

    async def test_create_chatroom(self, client: AsyncClient, test_analyst: User):
        """Creating a chatroom returns 201 with the chatroom data."""
        response = await client.post(
            "/chatrooms",
            headers=auth_headers(test_analyst),
            json={"name": "My First Chat"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My First Chat"
        assert "id" in data
        assert "created_at" in data

    async def test_list_chatrooms(
        self, client: AsyncClient, test_analyst: User, test_chatroom: Chatroom
    ):
        """Listing chatrooms returns the user's chatrooms."""
        response = await client.get(
            "/chatrooms",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(c["id"] == str(test_chatroom.id) for c in data)

    async def test_list_chatrooms_empty(
        self, client: AsyncClient, test_data_owner: User
    ):
        """A user with no chatrooms gets an empty list."""
        response = await client.get(
            "/chatrooms",
            headers=auth_headers(test_data_owner),
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_chatroom_empty_name(
        self, client: AsyncClient, test_analyst: User
    ):
        """Creating a chatroom with an empty name returns 422."""
        response = await client.post(
            "/chatrooms",
            headers=auth_headers(test_analyst),
            json={"name": ""},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestMessageHistory:
    """Tests for message history retrieval."""

    async def test_get_messages_empty(
        self, client: AsyncClient, test_analyst: User, test_chatroom: Chatroom
    ):
        """A new chatroom has no messages."""
        response = await client.get(
            f"/chatrooms/{test_chatroom.id}/messages",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_messages_wrong_chatroom(
        self, client: AsyncClient, test_analyst: User
    ):
        """Requesting messages for a non-existent chatroom returns 404."""
        import uuid

        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/chatrooms/{fake_id}/messages",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 404

    async def test_get_messages_invalid_id(
        self, client: AsyncClient, test_analyst: User
    ):
        """Requesting messages with an invalid UUID returns 400."""
        response = await client.get(
            "/chatrooms/not-a-uuid/messages",
            headers=auth_headers(test_analyst),
        )
        assert response.status_code == 400


@pytest.mark.asyncio
class TestChatroomAccessControl:
    """Tests for chatroom isolation between users."""

    async def test_cannot_access_other_users_chatroom(
        self,
        client: AsyncClient,
        test_data_owner: User,
        test_chatroom: Chatroom,
    ):
        """A user cannot view messages in another user's chatroom."""
        response = await client.get(
            f"/chatrooms/{test_chatroom.id}/messages",
            headers=auth_headers(test_data_owner),
        )
        assert response.status_code == 404

    async def test_cannot_send_to_other_users_chatroom(
        self,
        client: AsyncClient,
        test_data_owner: User,
        test_chatroom: Chatroom,
    ):
        """A user cannot send messages to another user's chatroom."""
        response = await client.post(
            f"/chatrooms/{test_chatroom.id}/message",
            headers=auth_headers(test_data_owner),
            json={"query": "What is total revenue?"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestSendMessage:
    """Tests for the SSE streaming message endpoint."""

    async def test_send_message_returns_sse(
        self, client: AsyncClient, test_analyst: User, test_chatroom: Chatroom
    ):
        """Sending a message returns a text/event-stream response."""
        response = await client.post(
            f"/chatrooms/{test_chatroom.id}/message",
            headers=auth_headers(test_analyst),
            json={"query": "What is the total transaction volume?"},
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    async def test_send_empty_query(
        self, client: AsyncClient, test_analyst: User, test_chatroom: Chatroom
    ):
        """Sending an empty query returns 422."""
        response = await client.post(
            f"/chatrooms/{test_chatroom.id}/message",
            headers=auth_headers(test_analyst),
            json={"query": ""},
        )
        assert response.status_code == 422
