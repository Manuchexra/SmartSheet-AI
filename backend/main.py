"""
SmartSheet AI — FastAPI ilovaning kirish nuqtasi.

Bu fayl:
1. FastAPI ilovasini yaratadi
2. CORS sozlaydi
3. Asosiy endpointlarni ulaydi (health, root)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# ============================================
# FastAPI ilovasini yaratish
# ============================================
app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Spreadsheet Generator — MVP 1.0",
    version="1.0.0-MVP",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================
# CORS sozlamalari
# ============================================
# MVP uchun barcha originlarga ruxsat.
# 10-bosqichda aniq originlarga cheklanadi.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Health Check — GET /api/v1/health
# ============================================
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """
    Server ishlayotganini tekshirish.
    
    Docker health check ham shu endpointni chaqiradi.
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": "1.0.0-MVP",
    }


# ============================================
# Root — GET /
# ============================================
@app.get("/", tags=["Root"])
async def root():
    """Bosh sahifa — API haqida qisqa ma'lumot."""
    return {
        "message": "SmartSheet AI API",
        "version": "1.0.0-MVP",
        "docs": "/docs",
        "health": "/api/v1/health",
    }