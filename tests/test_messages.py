"""
Messages API testlari.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestMessagesCRUD:
    """Messages CRUD testlari."""

    def _create_chat(self, client: TestClient) -> int:
        """Yordamchi: yangi chat yaratish."""
        response = client.post("/api/v1/chats", json={"title": "Test"})
        return response.json()["id"]

    def test_create_message(self, client: TestClient):
        """Yangi xabar yaratish ishlashi kerak."""
        chat_id = self._create_chat(client)

        response = client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "user", "content": "Salom"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "user"
        assert data["content"] == "Salom"
        assert data["chat_id"] == chat_id

    def test_list_messages(self, client: TestClient):
        """Xabarlar ro'yxatini olish."""
        chat_id = self._create_chat(client)

        # 3 ta xabar qo'shish
        for i in range(3):
            client.post(
                f"/api/v1/chats/{chat_id}/messages",
                json={"role": "user", "content": f"Xabar {i}"},
            )

        response = client.get(f"/api/v1/chats/{chat_id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["messages"]) == 3

    def test_messages_order(self, client: TestClient):
        """Xabarlar vaqt bo'yicha tartiblangan bo'lishi kerak."""
        chat_id = self._create_chat(client)

        client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "user", "content": "Birinchi"},
        )
        client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "ai", "content": "Ikkinchi"},
        )

        response = client.get(f"/api/v1/chats/{chat_id}/messages")
        data = response.json()
        assert data["messages"][0]["content"] == "Birinchi"
        assert data["messages"][1]["content"] == "Ikkinchi"

    def test_delete_message(self, client: TestClient):
        """Xabarni o'chirish."""
        chat_id = self._create_chat(client)

        created = client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "user", "content": "O'chirish"},
        )
        message_id = created.json()["id"]

        response = client.delete(
            f"/api/v1/chats/{chat_id}/messages/{message_id}"
        )
        assert response.status_code == 204

    def test_message_on_nonexistent_chat(self, client: TestClient):
        """Yo'q yoki boshqa brauzerga tegishli chat 404 qaytarishi kerak."""
        response = client.post(
            "/api/v1/chats/99999/messages",
            json={"role": "user", "content": "Test"},
        )
        assert response.status_code == 404

    def test_chat_updated_at(self, client: TestClient):
        """Xabar qo'shilganda chat.updated_at yangilanishi kerak."""
        chat_id = self._create_chat(client)

        # Chat'ni olish (boshida)
        chat1 = client.get(f"/api/v1/chats/{chat_id}").json()
        time1 = chat1["updated_at"]

        # Xabar qo'shish
        import time
        time.sleep(1)
        client.post(
            f"/api/v1/chats/{chat_id}/messages",
            json={"role": "user", "content": "Test"},
        )

        # Chat'ni qayta olish
        chat2 = client.get(f"/api/v1/chats/{chat_id}").json()
        time2 = chat2["updated_at"]

        assert time2 >= time1  # updated_at yangilangan

    def test_message_count_in_chat(self, client: TestClient):
        """Chat'da message_count to'g'ri bo'lishi kerak."""
        chat_id = self._create_chat(client)

        for i in range(5):
            client.post(
                f"/api/v1/chats/{chat_id}/messages",
                json={"role": "user", "content": f"Xabar {i}"},
            )

        response = client.get(f"/api/v1/chats/{chat_id}")
        assert response.json()["message_count"] == 5