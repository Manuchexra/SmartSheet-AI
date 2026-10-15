"""
SmartSheet AI — FastAPI ilovaning kirish nuqtasi.

Bu fayl:
1. FastAPI ilovasini yaratadi.
2. CORS, xavfsizlik header'larini sozlaydi.
3. Logging sozlaydi.
4. Static fayllarni (frontend) xizmat qildiradi.
5. API routerlarni ulaydi.
"""

import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.router import api_router
from backend.config import settings
from backend.db.migrations import upgrade_database


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
# FRONTEND PAPKASI
# ============================================
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
    openapi_url="/openapi.json",
)


# ============================================
# CORS — FAQAT RUXSAT ETILGAN ORIGINLAR
# ============================================
# Development'da localhost; production'da aniq domenlar
if settings.app_env == "development":
    allowed_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
else:
    # Production'da — faqat aniq domenlar
    allowed_origins = [
        # "https://smartsheet-ai.example.com",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Client-ID"],
    max_age=600,  # 10 daqiqa preflight cache
)


# ============================================
# GZIP — javoblarni siqish
# ============================================
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ============================================
# XAVFSIZLIK HEADER'LARI + REQUEST LOGGING
# ============================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Har bir javobga xavfsizlik header'larini qo'shadi.
    Shuningdek, so'rov vaqtini o'lchaydi.
    """
    start_time = time.time()

    response = await call_next(request)

    # Xavfsizlik header'lari
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # Request vaqtini log qilish (faqat API uchun)
    if request.url.path.startswith("/api/"):
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"{request.method} {request.url.path} — "
            f"{response.status_code} — {duration_ms:.1f}ms"
        )

    return response


# ============================================
# GLOBAL XATO USHLAGICH
# ============================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Kutilmagan xatolarni ushlash.

    Foydalanuvchiga tushunarli xabar, maxfiy ma'lumotsiz.
    """
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
if FRONTEND_DIR.exists():
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
        return {
            "message": "SmartSheet AI API",
            "note": "Frontend papkasi topilmadi",
            "docs": "/docs",
        }


# ============================================
# STARTUP
# ============================================
@app.on_event("startup")
async def startup_event():
    """Ilova ishga tushganda holatini log qilish."""
    upgrade_database()
    logger.info(f"🚀 {settings.app_name} ishga tushdi")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   AI provider: {settings.ai_provider or 'DEMO rejim'}")
    logger.info(f"   AI model: {settings.ai_model or '—'}")
    logger.info(
        f"   Limits: {settings.max_rows} qator × {settings.max_columns} ustun"
    )
    logger.info(f"   Frontend: http://localhost:8000/")
    logger.info(f"   Docs: http://localhost:8000/docs")

    # Ma'lumotlar bazasi sxemasini Alembic boshqaradi.
    if settings.app_env == "development":
        logger.info(f"   Database: {settings.database_url}")
        logger.info(f"   Migratsiya: alembic upgrade head")