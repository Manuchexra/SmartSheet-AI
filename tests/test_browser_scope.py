"""Browser-level isolation for chat data."""

from fastapi.testclient import TestClient

from backend.db.session import SessionLocal
from backend.models import Chat


OTHER_BROWSER_ID = "22222222-2222-4222-8222-222222222222"


def test_chats_and_nested_resources_are_scoped_to_browser(client: TestClient):
    created = client.post("/api/v1/chats", json={"title": "Browser scoped"})
    assert created.status_code == 201
    chat_id = created.json()["id"]

    other = TestClient(
        client.app,
        headers={"X-Client-ID": OTHER_BROWSER_ID},
    )
    assert all(
        response.status_code == 404
        for response in (
            other.get(f"/api/v1/chats/{chat_id}"),
            other.get(f"/api/v1/chats/{chat_id}/messages"),
            other.get(f"/api/v1/chats/{chat_id}/table"),
            other.post(
                f"/api/v1/chats/{chat_id}/messages",
                json={"role": "user", "content": "unauthorized"},
            ),
            other.put(
                f"/api/v1/chats/{chat_id}/table",
                json={
                    "title": "Unauthorized",
                    "columns": ["A"],
                    "rows": [["B"]],
                },
            ),
            other.delete(f"/api/v1/chats/{chat_id}"),
        )
    )
    assert all(
        chat["id"] != chat_id for chat in other.get("/api/v1/chats").json()["chats"]
    )

    assert client.get(f"/api/v1/chats/{chat_id}").status_code == 200
    assert client.delete(f"/api/v1/chats/{chat_id}").status_code == 204


def test_first_browser_claims_legacy_chats(client: TestClient):
    with SessionLocal() as db:
        chat = Chat(title="Legacy chat")
        db.add(chat)
        db.commit()
        chat_id = chat.id

    claiming_browser = TestClient(
        client.app,
        headers={"X-Client-ID": OTHER_BROWSER_ID},
    )
    chats = claiming_browser.get("/api/v1/chats").json()["chats"]
    assert any(item["id"] == chat_id for item in chats)
    assert all(
        item["id"] != chat_id for item in client.get("/api/v1/chats").json()["chats"]
    )
    assert claiming_browser.delete(f"/api/v1/chats/{chat_id}").status_code == 204
