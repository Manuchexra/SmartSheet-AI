"""
Chat generate (AI) testlari.
"""

from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from backend.modules.ai.schemas import AIResponse


@pytest.mark.api
class TestChatGenerate:
    """Chat generate testlari."""

    def _create_chat(self, client: TestClient, title: str = "Test") -> int:
        response = client.post("/api/v1/chats", json={"title": title})
        return response.json()["id"]

    @patch("backend.api.endpoints.chats.generate_edit_with_ai")
    def test_uploaded_table_is_available_to_following_ai_edit(
        self, mock_edit, client: TestClient
    ):
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Xodimlar"
        worksheet.append(["Ism", "Maosh"])
        worksheet.append(["Ali", 5000])
        file_content = BytesIO()
        workbook.save(file_content)

        chat_id = self._create_chat(client, title="Yangi chat")
        upload_response = client.post(
            f"/api/v1/chats/{chat_id}/table/upload",
            files={
                "file": (
                    "xodimlar.xlsx",
                    file_content.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )
        assert upload_response.status_code == 200

        mock_edit.return_value = (
            AIResponse(
                title="Xodimlar",
                columns=["Ism", "Maosh"],
                rows=[["Ali", 5500]],
            ),
            "ai",
        )
        response = client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "Maoshni 10 foiz oshir"},
        )

        assert response.status_code == 200
        assert response.json()["table"]["rows"] == [["Ali", 5500]]
        existing_table = mock_edit.call_args.kwargs["existing_table"]
        assert existing_table["columns"] == ["Ism", "Maosh"]
        assert existing_table["rows"] == [["Ali", 5000]]

    @patch("backend.api.endpoints.chats.generate_with_ai")
    def test_generate_first_time(self, mock_ai, client: TestClient):
        """Birinchi marta — jadval yaratish."""
        mock_ai.return_value = (
            AIResponse(
                title="Xodimlar",
                columns=["Ism", "Maosh"],
                rows=[["Ali", 5000], ["Vali", 4000]],
            ),
            "ai",
        )

        chat_id = self._create_chat(client, title="Yangi chat")
        response = client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "5 ta xodim uchun jadval yarat"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"]["version"] == 1
        assert data["table"]["title"] == "Xodimlar"
        assert data["table"]["row_count"] == 2
        assert data["user_message"]["role"] == "user"
        assert data["ai_message"]["role"] == "ai"
        assert data["chat"]["title"] == "Xodimlar"

        chat_response = client.get(f"/api/v1/chats/{chat_id}")
        assert chat_response.json()["title"] == "Xodimlar"

    @patch("backend.api.endpoints.chats.generate_edit_with_ai")
    @patch("backend.api.endpoints.chats.generate_with_ai")
    def test_generate_edit_existing(
        self, mock_generate, mock_edit, client: TestClient
    ):
        """Jadval mavjud bo'lsa — edit rejimi."""
        # Birinchi jadval
        mock_generate.return_value = (
            AIResponse(
                title="Xodimlar",
                columns=["Ism", "Maosh"],
                rows=[["Ali", 5000]],
            ),
            "ai",
        )
        chat_id = self._create_chat(client)
        client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "Jadval yarat"},
        )

        # Edit
        mock_edit.return_value = (
            AIResponse(
                title="Xodimlar",
                columns=["Ism", "Maosh"],
                rows=[["Ali", 5500]],  # 10% oshgan
            ),
            "ai",
        )
        response = client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "Maoshni 10% oshir"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["table"]["version"] == 2  # OSHGAN
        assert data["table"]["rows"][0][1] == 5500

        # Edit chaqirilganini tekshirish
        mock_edit.assert_called_once()

    def test_generate_nonexistent_chat(self, client: TestClient):
        """Yo'q chatga generate — 404."""
        response = client.post(
            "/api/v1/chats/99999/generate",
            json={"prompt": "Test"},
        )
        assert response.status_code == 404

    def test_generate_empty_prompt(self, client: TestClient):
        """Bo'sh prompt — 422."""
        chat_id = self._create_chat(client)
        response = client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": ""},
        )
        assert response.status_code == 422

    def test_generate_gibberish_prompt_is_rejected(self, client: TestClient):
        """Tushunarsiz so'rovga jadval yaratilmasligi kerak."""
        chat_id = self._create_chat(client, title="Yangi chat")
        response = client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "kfddf"},
        )

        assert response.status_code == 422
        assert "So'rov tushunarsiz" in response.json()["detail"][0]["msg"]

        messages = client.get(
            f"/api/v1/chats/{chat_id}/messages"
        ).json()["messages"]
        assert messages == []

        table_response = client.get(f"/api/v1/chats/{chat_id}/table")
        assert table_response.status_code == 404

    def test_generate_greeting_does_not_create_sample_data(
        self, client: TestClient
    ):
        """Oddiy salomlashuv namuna ma'lumotli jadval yaratmasligi kerak."""
        chat_id = self._create_chat(client, title="Yangi chat")

        response = client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "salom"},
        )

        assert response.status_code == 200
        table = response.json()["table"]
        assert table["title"] == "salom"
        assert table["columns"] == ["Matn"]
        assert table["rows"] == [["salom"]]

    @patch("backend.api.endpoints.chats.generate_with_ai")
    def test_generate_saves_messages(self, mock_ai, client: TestClient):
        """Generate xabarlarni saqlashi kerak."""
        mock_ai.return_value = (
            AIResponse(
                title="Test",
                columns=["A"],
                rows=[["1"]],
            ),
            "ai",
        )
        chat_id = self._create_chat(client)
        client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "Test prompt"},
        )

        # Xabarlar tekshirish
        response = client.get(f"/api/v1/chats/{chat_id}/messages")
        messages = response.json()["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "ai"

    @patch("backend.api.endpoints.chats.generate_with_ai")
    def test_generate_creates_table(self, mock_ai, client: TestClient):
        """Generate jadvalni saqlashi kerak."""
        mock_ai.return_value = (
            AIResponse(
                title="Test",
                columns=["A", "B"],
                rows=[["1", "2"]],
            ),
            "ai",
        )
        chat_id = self._create_chat(client)
        client.post(
            f"/api/v1/chats/{chat_id}/generate",
            json={"prompt": "Test"},
        )

        # Jadval tekshirish
        response = client.get(f"/api/v1/chats/{chat_id}/table")
        assert response.status_code == 200
        assert response.json()["title"] == "Test"