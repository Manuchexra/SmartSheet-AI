"""
API endpoint testlari.

Bu testlar:
- Health check
- Root
- Jadval yaratish (mock AI bilan)
- Validatsiya xatolari
"""

import pytest


# ============================================
# HEALTH CHECK
# ============================================
@pytest.mark.api
class TestHealthCheck:
    """Health check endpoint."""

    def test_health_ok(self, client):
        """Health endpoint 200 qaytarishi kerak."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data


# ============================================
# ROOT
# ============================================
@pytest.mark.api
class TestRoot:
    """Root endpoint."""

    def test_root_ok(self, client):
        """Root endpoint HTML yoki JSON qaytarishi kerak."""
        response = client.get("/")
        # Frontend mavjud bo'lsa HTML, bo'lmasa JSON
        assert response.status_code == 200


# ============================================
# JADVAL YARATISH — MOCK AI BILAN
# ============================================
@pytest.mark.api
@pytest.mark.integration
class TestGenerateTable:
    """POST /api/v1/tables/generate."""

    def test_generate_success(self, client, mock_ai_service):
        """Mock AI bilan jadval yaratilishi kerak."""
        response = client.post(
            "/api/v1/tables/generate",
            json={"prompt": "5 ta xodim uchun jadval yarat"},
        )
        assert response.status_code == 200
        data = response.json()

        # Asosiy maydonlar
        assert "title" in data
        assert "columns" in data
        assert "rows" in data
        assert "row_count" in data
        assert "column_count" in data
        assert "source" in data

        # Tuzilma mosligi
        assert data["row_count"] == len(data["rows"])
        assert data["column_count"] == len(data["columns"])
        for row in data["rows"]:
            assert len(row) == data["column_count"]

        # Mock AI ishlatilgan
        assert data["source"] == "ai"

    def test_generate_demo_fallback(self, client, mock_ai_unavailable):
        """AI mavjud emas bo'lsa, demo rejim ishlashi kerak."""
        response = client.post(
            "/api/v1/tables/generate",
            json={"prompt": "talabalar uchun jadval yarat"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "demo"

    def test_generate_empty_prompt(self, client):
        """Bo'sh prompt 422 qaytarishi kerak."""
        response = client.post(
            "/api/v1/tables/generate",
            json={"prompt": ""},
        )
        assert response.status_code == 422

    def test_generate_short_prompt(self, client):
        """Juda qisqa prompt 422 qaytarishi kerak."""
        response = client.post(
            "/api/v1/tables/generate",
            json={"prompt": "ab"},
        )
        assert response.status_code == 422

    def test_generate_missing_prompt(self, client):
        """Prompt yo'q bo'lsa 422 qaytarishi kerak."""
        response = client.post(
            "/api/v1/tables/generate",
            json={},
        )
        assert response.status_code == 422

    def test_generate_long_prompt(self, client):
        """Juda uzun prompt 422 qaytarishi kerak."""
        response = client.post(
            "/api/v1/tables/generate",
            json={"prompt": "a" * 3000},
        )
        assert response.status_code == 422


# ============================================
# AI XATOSI — FALLBACK
# ============================================
@pytest.mark.api
class TestAIFallback:
    """AI xatosi bo'lsa, demo rejimga fallback."""

    def test_ai_error_fallback(self, client, monkeypatch):
        """AI xatosi bo'lsa, demo javob qaytarilishi kerak."""
        from backend.modules.ai.schemas import AIError

        def fake_generate(request):
            raise AIError("Test xatosi", code="test")

        monkeypatch.setattr(
            "backend.api.endpoints.table.generate_with_ai",
            fake_generate,
        )

        response = client.post(
            "/api/v1/tables/generate",
            json={"prompt": "talabalar uchun jadval"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "demo"