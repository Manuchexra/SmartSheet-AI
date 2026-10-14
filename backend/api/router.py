"""
API router — barcha endpointlarni birlashtiradi.

Prefiks: /api/v1
"""

from fastapi import APIRouter

from backend.api.endpoints import table, excel


# ============================================
# ASOSIY ROUTER
# ============================================
api_router = APIRouter(prefix="/api/v1")


# ============================================
# MODUL ROUTERLARINI ULASH
# ============================================
api_router.include_router(table.router)
api_router.include_router(excel.router)