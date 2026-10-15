"""
Tables CRUD API testlari.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestTablesCRUD:
    """Tables CRUD testlari."""

    def _create_chat(self, client: TestClient) -> int:
        response = client.post("/api/v1/chats", json={"title": "Test"})
        return response.json()["id"]

    def test_create_table(self, client: TestClient):
        """Jadval yaratish ishlashi kerak."""
        chat_id = self._create_chat(client)

        response = client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={
                "title": "Test",
                "columns": ["A", "B"],
                "rows": [["1", "2"]],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test"
        assert data["row_count"] == 1
        assert data["column_count"] == 2
        assert data["version"] == 1

    def test_get_table(self, client: TestClient):
        """Jadvalni olish."""
        chat_id = self._create_chat(client)
        client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={
                "title": "Test",
                "columns": ["A"],
                "rows": [["1"]],
            },
        )

        response = client.get(f"/api/v1/chats/{chat_id}/table")
        assert response.status_code == 200
        assert response.json()["title"] == "Test"

    def test_create_table_twice_fails(self, client: TestClient):
        """Ikki marta jadval yaratish xato berishi kerak."""
        chat_id = self._create_chat(client)

        client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={"title": "T", "columns": ["A"], "rows": [["1"]]},
        )

        response = client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={"title": "T2", "columns": ["B"], "rows": [["2"]]},
        )
        assert response.status_code == 400

    def test_upsert_table(self, client: TestClient):
        """PUT — yaratish yoki yangilash."""
        chat_id = self._create_chat(client)

        # 1-marta — yaratadi
        response = client.put(
            f"/api/v1/chats/{chat_id}/table",
            json={"title": "T1", "columns": ["A"], "rows": [["1"]]},
        )
        assert response.status_code == 200
        assert response.json()["version"] == 1

        # 2-marta — yangilaydi
        response = client.put(
            f"/api/v1/chats/{chat_id}/table",
            json={"title": "T2", "columns": ["A", "B"], "rows": [["1", "2"]]},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "T2"
        assert response.json()["version"] == 2

    def test_update_table(self, client: TestClient):
        """Jadvalni tahrirlash."""
        chat_id = self._create_chat(client)
        client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={"title": "T", "columns": ["A"], "rows": [["1"]]},
        )

        response = client.patch(
            f"/api/v1/chats/{chat_id}/table",
            json={"rows": [["1"], ["2"]]},
        )
        assert response.status_code == 200
        assert response.json()["row_count"] == 2
        assert response.json()["version"] == 2

    def test_delete_table(self, client: TestClient):
        """Jadvalni o'chirish."""
        chat_id = self._create_chat(client)
        client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={"title": "T", "columns": ["A"], "rows": [["1"]]},
        )

        response = client.delete(f"/api/v1/chats/{chat_id}/table")
        assert response.status_code == 204

        # Tekshirish
        response = client.get(f"/api/v1/chats/{chat_id}/table")
        assert response.status_code == 404

    def test_get_nonexistent_table(self, client: TestClient):
        """Yo'q jadval 404 qaytarishi kerak."""
        chat_id = self._create_chat(client)
        response = client.get(f"/api/v1/chats/{chat_id}/table")
        assert response.status_code == 404

    def test_table_with_formulas(self, client: TestClient):
        """Formulali jadval yaratish."""
        chat_id = self._create_chat(client)

        response = client.post(
            f"/api/v1/chats/{chat_id}/table",
            json={
                "title": "Talabalar",
                "columns": ["Ism", "Ball", "Natija"],
                "rows": [
                    ["Ali", 92, '=IF(B2>60,"O\'tdi","Yiqildi")'],
                    ["Vali", 45, '=IF(B3>60,"O\'tdi","Yiqildi")'],
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["has_formulas"] is True
        assert data["formula_count"] == 2