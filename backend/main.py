"""
SmartSheet AI — FastAPI ilovaning kirish nuqtasi.

Bu fayl:
1. FastAPI ilovasini yaratadi.
2. CORS sozlaydi.
3. Logging sozlaydi.
4. Static fayllarni (frontend) xizmat qildiradi.
5. API routerlarni ulaydi.
"""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.config import settings


# ============================================
# LOGGING
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================
# FRONTEND PAPKASINI TOPISH
# ============================================
# backend/main.py dan ikki pog'ona yuqoriga: backend/ → ildiz
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================
# FASTAPI ILOVASI
# ============================================
app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Spreadsheet Generator — MVP 1.0",
    version="1.0.0-MVP",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================
# CORS
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 10-bosqichda cheklanadi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# GLOBAL XATO USHLAGICH
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Kutilmagan xatoliklarni ushlash."""
    logger.error(f"Kutilmagan xato: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Serverda kutilmagan xatolik yuz berdi. "
                      "Iltimos, keyinroq qayta urinib ko'ring."
        },
    )


# ============================================
# API ROUTERLAR
# ============================================
app.include_router(api_router)


# ============================================
# HEALTH CHECK
# ============================================
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Server ishlayotganini tekshirish."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "version": "1.0.0-MVP",
    }


# ============================================
# STATIC FAYLLAR (FRONTEND)
# ============================================
# Diqqat: bu eng oxirida bo'lishi kerak!
# Aks holda u barcha API yo'llarini "yutib yuboradi".

if FRONTEND_DIR.exists():
    # /css, /js, /assets — static fayllar
    app.mount(
        "/css",
        StaticFiles(directory=FRONTEND_DIR / "css"),
        name="css",
    )
    app.mount(
        "/js",
        StaticFiles(directory=FRONTEND_DIR / "js"),
        name="js",
    )
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIR / "assets"),
        name="assets",
    )

    # / — index.html
    @app.get("/", include_in_schema=False)
    async def serve_index():
        """Bosh sahifa — index.html."""
        from fastapi.responses import FileResponse
        return FileResponse(FRONTEND_DIR / "index.html")

    logger.info(f"✅ Frontend xizmat qilinadi: {FRONTEND_DIR}")
else:
    logger.warning(f"⚠️  Frontend papkasi topilmadi: {FRONTEND_DIR}")

    @app.get("/", include_in_schema=False)
    async def root_fallback():
        """Frontend yo'q bo'lsa, API ma'lumotlarini qaytarish."""
        return {
            "message": "SmartSheet AI API",
            "note": "Frontend papkasi topilmadi",
            "docs": "/docs",
            "health": "/api/v1/health",
        }


# ============================================
# STARTUP
# ============================================
@app.on_event("startup")
async def startup_event():
    """Ilova ishga tushganda log yozish."""
    logger.info(f"🚀 {settings.app_name} ishga tushdi")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   AI provider: {settings.ai_provider or 'DEMO rejim'}")
    logger.info(f"   Limits: {settings.max_rows} qator × {settings.max_columns} ustun")
    if FRONTEND_DIR.exists():
        logger.info(f"   Frontend: http://localhost:8000/")
    logger.info(f"   Docs: http://localhost:8000/docs")