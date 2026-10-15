"""
SQLAlchemy Base klassi.

Barcha modellar shu Base'dan meros oladi.
Bu — SQLAlchemy'ning "Object-Relational Mapping" tamoyili.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Barcha modellar uchun asosiy klass.

    SQLAlchemy 2.0 uslubi:
    - `Mapped[T]` — type hint
    - `mapped_column()` — ustun sozlamalari
    """
    pass


class TimestampMixin:
    """
    Mixin: created_at va updated_at ustunlari.

    Har bir modelga qo'shish mumkin:
        class MyModel(Base, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )