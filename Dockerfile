# ============================================
# SmartSheet AI — Backend Dockerfile
# ============================================

# Python 3.11 "slim" versiyasidan foydalanamiz
# slim = yengil, kichik hajmli image
FROM python:3.11-slim

# Metadata
LABEL maintainer="SmartSheet AI Team"
LABEL description="AI-Powered Spreadsheet Generator"

# Python optimizatsiyalari:
# PYTHONDONTWRITEBYTECODE = .pyc fayllar yaratilmasin
# PYTHONUNBUFFERED = log'lar darhol chiqarilsin (Docker uchun muhim)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Ish papkasi
WORKDIR /app

# Tizim paketlari (openpyxl va boshqalar uchun kerak bo'lishi mumkin)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Avval faqat requirements.txt nusxalaymiz (Docker cache uchun muhim!)
# Agar kod o'zgarsa, paketlar qayta o'rnatilmaydi
COPY requirements.txt .

# Paketlarni o'rnatamiz
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Endi butun loyihani nusxalaymiz
COPY . .

# Port ochamiz
EXPOSE 8000

# Health check (Docker konteyner tirikligini tekshiradi)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Serverni ishga tushirish
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]