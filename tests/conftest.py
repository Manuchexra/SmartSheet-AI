"""
Umumiy pytest fixture'lari.

Bu fayl barcha testlarda ishlatiladigan fixture'larni saqlaydi:
- FastAPI TestClient
- Namuna TableData
- Namuna AIResponse
- Mock AI (haqiqiy AI'ga so'rov yubormaslik uchun)
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.modules.ai.schemas import AIResponse
from backend.modules.table_generator.schemas import TableData


# ============================================
# FASTAPI TEST CLIENT
# ============================================
@pytest.fixture
def client() -> Iterator[TestClient]:
    """
    FastAPI TestClient.

    Haqiqiy server ishga tushirmasdan, HTTP so'rovlarni simulyatsiya qiladi.
    """
    with TestClient(
        app,
        headers={"X-Client-ID": "11111111-1111-4111-8111-111111111111"},
    ) as test_client:
        yield test_client


# ============================================
# NAMUNA MA'LUMOTLAR
# ============================================
@pytest.fixture
def sample_table_data() -> TableData:
    """Namuna TableData — 3 ustun, 3 qator."""
    return TableData(
        title="Test jadval",
        columns=["Ism", "Lavozim", "Maosh"],
        rows=[
            ["Ali Karimov", "Dasturchi", 5000],
            ["Malika Azizova", "Dizayner", 4500],
            ["Sardor Toshmatov", "Menejer", 6000],
        ],
    )


@pytest.fixture
def sample_ai_response() -> AIResponse:
    """Namuna AIResponse — AI'dan kelgan xom javob."""
    return AIResponse(
        title="Test jadval",
        columns=["Ism", "Lavozim", "Maosh"],
        rows=[
            ["Ali Karimov", "Dasturchi", 5000],
            ["Malika Azizova", "Dizayner", 4500],
        ],
    )


@pytest.fixture
def sample_ai_raw_json() -> str:
    """AI'dan kelgan xom JSON (markdown fence bilan)."""
    return """```json
{
  "title": "Talabalar",
  "columns": ["Ism", "Ball"],
  "rows": [["Ali", 92], ["Malika", 85]]
}
```"""


@pytest.fixture
def sample_ai_raw_json_no_fence() -> str:
    """AI'dan kelgan xom JSON (fencesiz, oldida matn bilan)."""
    return """Mana sizning jadvalingiz:
{"title": "Talabalar", "columns": ["Ism", "Ball"], "rows": [["Ali", 92]]}"""


# ============================================
# MOCK AI (haqiqiy AI'ga so'rov yubormaslik)
# ============================================
@pytest.fixture
def mock_ai_service(monkeypatch, sample_ai_response):
    """
    AI service'ni mock qilish.

    Haqiqiy Groq/OpenAI'ga so'rov yubormaydi — namuna javob qaytaradi.
    Bu testlarni tez va ishonchli qiladi.
    """
    def fake_generate(request):
        return sample_ai_response, "ai"

    monkeypatch.setattr(
        "backend.modules.ai.service.generate_with_ai",
        fake_generate,
    )

    # Endpoint'dagi import ham yangilanishi kerak
    monkeypatch.setattr(
        "backend.api.endpoints.table.generate_with_ai",
        fake_generate,
    )

    return fake_generate


@pytest.fixture
def mock_ai_unavailable(monkeypatch):
    """
    AI mavjud emas holatini mock qilish.

    `is_ai_available()` False qaytaradi — demo rejim ishga tushadi.
    """
    monkeypatch.setattr(
        "backend.modules.ai.service.is_ai_available",
        lambda: False,
    )