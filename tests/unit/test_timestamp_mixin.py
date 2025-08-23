"""Модульные тесты для TimestampMixin."""

import pytest
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

from app.dao.mixins.id_mixin import IdMixin
from app.dao.mixins.timestamp_mixin import TimestampMixin


class TestTimestampMixin:
    """Тесты для TimestampMixin."""

    @pytest.mark.unit
    def test_timestamp_fields_attributes(self) -> None:
        """Проверяет атрибуты полей временных меток."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем поле created_at
        created_at_column = TestModel.__table__.columns["created_at"]
        assert str(created_at_column.type) == "TIMESTAMP"
        assert created_at_column.server_default is not None

        # Проверяем поле updated_at
        updated_at_column = TestModel.__table__.columns["updated_at"]
        assert str(updated_at_column.type) == "TIMESTAMP"
        assert updated_at_column.server_default is not None
        assert updated_at_column.onupdate is not None

    def test_timestamp_fields_type_annotations(self) -> None:
        """Проверяет типизацию полей временных меток."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем что поля доступны
        assert hasattr(TestModel, "created_at")
        assert hasattr(TestModel, "updated_at")

    def test_timestamp_fields_inheritance(self) -> None:
        """Проверяет что TimestampMixin корректно наследуется."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем что поля доступны
        assert hasattr(TestModel, "created_at")
        assert hasattr(TestModel, "updated_at")
        assert TestModel.created_at is not None
        assert TestModel.updated_at is not None

    def test_timestamp_fields_names(self) -> None:
        """Проверяет названия полей временных меток."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем названия полей
        assert "created_at" in TestModel.__table__.columns
        assert "updated_at" in TestModel.__table__.columns
