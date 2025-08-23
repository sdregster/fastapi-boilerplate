"""Базовый миксин с общими методами для моделей."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import inspect


class BaseMixin:
    """Базовый миксин с общими методами для всех моделей."""

    def to_dict(self, exclude_none: bool = False) -> dict[str, Any]:
        """Преобразует объект модели в словарь.

        Args:
            exclude_none: Исключать ли None значения из результата.

        Returns:
            dict[str, Any]: Словарь с данными объекта.
        """
        result = {}
        for column in inspect(self.__class__).columns:
            value = getattr(self, column.key)

            # Преобразование специальных типов данных
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = float(value)
            elif isinstance(value, uuid.UUID):
                value = str(value)

            # Добавляем значение в результат
            if not exclude_none or value is not None:
                result[column.key] = value

        return result

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта для удобства отладки.

        Returns:
            str: Строковое представление объекта.
        """
        id_val = getattr(self, "id", "N/A")
        created_at = getattr(self, "created_at", "N/A")
        updated_at = getattr(self, "updated_at", "N/A")
        return (
            f"<{self.__class__.__name__}(id={id_val}, "
            f"created_at={created_at}, updated_at={updated_at})>"
        )
