"""Модульные тесты для IdMixin."""

import pytest
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

from app.dao.mixins.id_mixin import IdMixin


class TestIdMixin:
    """Тесты для IdMixin."""

    @pytest.mark.unit
    def test_id_field_attributes(self) -> None:
        """Проверяет атрибуты поля id."""
        # Создаем тестовую модель
        Base = declarative_base()

        class TestModel(Base, IdMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем атрибуты поля id
        id_column = TestModel.__table__.columns["id"]
        assert id_column.primary_key is True
        assert id_column.autoincrement is True
        assert str(id_column.type) == "INTEGER"

    def test_id_field_type_annotation(self) -> None:
        """Проверяет типизацию поля id."""
        Base = declarative_base()

        class TestModel(Base, IdMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем что поле id доступно и имеет правильный тип
        assert hasattr(TestModel, "id")
        assert TestModel.id is not None

    def test_id_field_inheritance(self) -> None:
        """Проверяет что IdMixin корректно наследуется."""
        Base = declarative_base()

        class TestModel(Base, IdMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем что поле id доступно
        assert hasattr(TestModel, "id")
        assert TestModel.id is not None
