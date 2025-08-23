"""Миксин для добавления поля id с автоинкрементом."""

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class IdMixin:
    """Миксин для добавления первичного ключа id с автоинкрементом.

    Attributes:
        id: Первичный ключ с автоинкрементом.
    """

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
