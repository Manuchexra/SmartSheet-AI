"""
Modellar paketi.

Bu paket barcha SQLAlchemy modellarini eksport qiladi.
Bu — modellarni bir joydan import qilish uchun qulaylik.
"""

from backend.models.chat import Chat
from backend.models.message import Message
from backend.models.table import Table

__all__ = [
    "Chat",
    "Message",
    "Table",
]