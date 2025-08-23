"""Интеграционные тесты для всех миксинов."""

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from app.dao.mixins.base_mixin import BaseMixin
from app.dao.mixins.id_mixin import IdMixin
from app.dao.mixins.timestamp_mixin import TimestampMixin

if TYPE_CHECKING:
    pass


class TestMixinsIntegration:
    """Интеграционные тесты для всех миксинов."""

    @pytest.mark.integration
    def test_all_mixins_together(self) -> None:
        """Проверяет что все миксины работают корректно вместе."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            age = Column(Integer)

        # Проверяем что все поля присутствуют
        assert hasattr(TestModel, "id")
        assert hasattr(TestModel, "created_at")
        assert hasattr(TestModel, "updated_at")
        assert hasattr(TestModel, "name")
        assert hasattr(TestModel, "age")

        # Проверяем что все методы доступны
        assert hasattr(TestModel, "to_dict")
        assert hasattr(TestModel, "__repr__")

    @pytest.mark.integration
    def test_mixin_order_importance(self) -> None:
        """Проверяет важность порядка наследования миксинов."""
        Base = declarative_base()

        # Правильный порядок: IdMixin, TimestampMixin, BaseMixin
        class CorrectModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "correct_model"
            name = Column(String(50))

        # Проверяем что все работает корректно
        model = CorrectModel()
        model.name = "Test"

        # Проверяем методы
        assert callable(model.to_dict)
        assert callable(model.__repr__)

        # Проверяем что to_dict возвращает все поля
        result = model.to_dict()
        expected_fields = ["id", "created_at", "updated_at", "name"]
        for field in expected_fields:
            assert field in result

    @pytest.mark.integration
    def test_mixin_methods_with_data(self) -> None:
        """Проверяет методы миксинов с реальными данными."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            description = Column(String(200))

        # Создаем экземпляр с данными
        model = TestModel()
        model.name = "Integration Test"
        model.description = "Testing all mixins together"

        # Устанавливаем datetime значения
        test_datetime = datetime(2023, 1, 1, 12, 0, 0)
        model.created_at = test_datetime
        model.updated_at = test_datetime

        # Тестируем to_dict
        result = model.to_dict()
        assert result["name"] == "Integration Test"
        assert result["description"] == "Testing all mixins together"
        assert result["created_at"] == "2023-01-01T12:00:00"
        assert result["updated_at"] == "2023-01-01T12:00:00"

        # Тестируем __repr__
        repr_str = repr(model)
        assert "TestModel" in repr_str
        assert "id=" in repr_str

    @pytest.mark.integration
    def test_mixin_inheritance_chain(self) -> None:
        """Проверяет цепочку наследования миксинов."""
        Base = declarative_base()

        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))

        # Проверяем MRO (Method Resolution Order)
        mro = TestModel.__mro__

        # Base должен быть первым
        assert mro[0] == TestModel
        # IdMixin, TimestampMixin, BaseMixin должны быть в MRO
        assert IdMixin in mro
        assert TimestampMixin in mro
        assert BaseMixin in mro

        # Проверяем что методы доступны через наследование
        assert hasattr(TestModel, "to_dict")
        assert hasattr(TestModel, "__repr__")
        assert hasattr(TestModel, "id")
        assert hasattr(TestModel, "created_at")
        assert hasattr(TestModel, "updated_at")
