"""Миксин для добавления полей временных меток."""

from datetime import datetime

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Миксин для добавления полей created_at и updated_at с автоматическим обновлением.

    Attributes:
        created_at: Время создания записи (устанавливается автоматически).
        updated_at: Время последнего обновления записи (обновляется автоматически).
    """

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
    )
