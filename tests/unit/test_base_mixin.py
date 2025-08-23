"""Модульные тесты для BaseMixin."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from app.dao.mixins.base_mixin import BaseMixin
from app.dao.mixins.id_mixin import IdMixin
from app.dao.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    pass


class TestBaseMixin:
    """Тесты для BaseMixin."""

    @pytest.mark.unit
    def test_to_dict_basic(self) -> None:
        """Проверяет базовый метод to_dict."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            age = Column(Integer)

        # Создаем экземпляр модели
        model = TestModel()
        model.name = "Test User"
        model.age = 25

        result = model.to_dict()

        # Проверяем что все поля присутствуют
        assert "id" in result
        assert "name" in result
        assert "age" in result
        assert "created_at" in result
        assert "updated_at" in result

        # Проверяем значения
        assert result["name"] == "Test User"
        assert result["age"] == 25

    def test_to_dict_exclude_none_true(self) -> None:
        """Проверяет метод to_dict с exclude_none=True."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            age = Column(Integer)

        # Создаем экземпляр модели с None значениями
        model = TestModel()
        model.name = "Test User"
        model.age = None

        result = model.to_dict(exclude_none=True)

        # Проверяем что None значения исключены
        assert "name" in result
        assert "age" not in result
        assert result["name"] == "Test User"

    def test_to_dict_exclude_none_false(self) -> None:
        """Проверяет метод to_dict с exclude_none=False."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            age = Column(Integer)

        # Создаем экземпляр модели с None значениями
        model = TestModel()
        model.name = "Test User"
        model.age = None

        result = model.to_dict(exclude_none=False)

        # Проверяем что None значения включены
        assert "name" in result
        assert "age" in result
        assert result["name"] == "Test User"
        assert result["age"] is None

    def test_to_dict_datetime_conversion(self) -> None:
        """Проверяет конвертацию datetime в to_dict."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Создаем экземпляр модели
        model = TestModel()
        model.name = "Test User"

        # Устанавливаем datetime значения
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        model.created_at = test_datetime
        model.updated_at = test_datetime

        result = model.to_dict()

        # Проверяем что datetime конвертированы в ISO формат
        assert result["created_at"] == "2023-01-01T12:00:00"
        assert result["updated_at"] == "2023-01-01T12:00:00"

    def test_to_dict_decimal_conversion(self) -> None:
        """Проверяет конвертацию Decimal в to_dict."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            price = Column(String(20))  # Используем String для хранения Decimal

        # Создаем экземпляр модели
        model = TestModel()
        model.name = "Test Product"

        # Устанавливаем Decimal значение
        test_decimal = Decimal("10.50")
        model.price = test_decimal

        result = model.to_dict()

        # Проверяем что Decimal конвертирован в float
        assert result["price"] == 10.5

    def test_to_dict_uuid_conversion(self) -> None:
        """Проверяет конвертацию UUID в to_dict."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            uuid_field = Column(String(36))  # Используем String для хранения UUID

        # Создаем экземпляр модели
        model = TestModel()
        model.name = "Test UUID"

        # Устанавливаем UUID значение
        test_uuid = uuid4()
        model.uuid_field = test_uuid

        result = model.to_dict()

        # Проверяем что UUID конвертирован в строку
        assert result["uuid_field"] == str(test_uuid)

    def test_repr_method(self) -> None:
        """Проверяет метод __repr__."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Создаем экземпляр модели
        model = TestModel()
        model.name = "Test User"

        repr_str = repr(model)

        # Проверяем что __repr__ возвращает строку
        assert isinstance(repr_str, str)
        assert "TestModel" in repr_str
        assert "id=" in repr_str
        assert "created_at=" in repr_str
        assert "updated_at=" in repr_str

    def test_mixin_inheritance(self) -> None:
        """Проверяет что BaseMixin корректно наследуется."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем что методы доступны
        assert hasattr(TestModel, "to_dict")
        assert hasattr(TestModel, "__repr__")
        assert callable(TestModel().to_dict)
        assert callable(TestModel().__repr__)
