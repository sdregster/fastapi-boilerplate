"""End-to-end тесты для полного рабочего процесса FastAPI приложения."""

import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dao.mixins.base_mixin import BaseMixin
from app.dao.mixins.id_mixin import IdMixin
from app.dao.mixins.timestamp_mixin import TimestampMixin


class TestFullWorkflow:
    """E2E тесты для полного рабочего процесса."""

    @pytest.fixture(scope="class")
    def engine(self):
        """Создает тестовый движок базы данных."""
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    @pytest.fixture(scope="class")
    def session_factory(self, engine):
        """Создает фабрику сессий."""
        return sessionmaker(autocommit=False, autoflush=False, bind=engine)

    @pytest.fixture(scope="class")
    def base_class(self, engine):
        """Создает базовый класс для моделей."""
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        # Создаем тестовую модель с миксинами
        class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
            __tablename__ = "test_model"
            name = Column(String(50))
            description = Column(String(200))
            value = Column(Integer)

        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        return Base, TestModel

    @pytest.mark.e2e
    def test_complete_model_lifecycle(self, session_factory, base_class):
        """Тестирует полный жизненный цикл модели с миксинами."""
        Base, TestModel = base_class
        session = session_factory()

        try:
            # 1. Создание модели
            model = TestModel(
                name="E2E Test Model", description="Testing complete workflow", value=42
            )

            # 2. Сохранение в базу данных
            session.add(model)
            session.commit()
            session.refresh(model)

            # 3. Проверяем что id установлен
            assert model.id is not None
            assert model.id > 0

            # 4. Проверяем что временные метки установлены
            assert model.created_at is not None
            assert model.updated_at is not None

            # 5. Проверяем метод to_dict
            model_dict = model.to_dict()
            assert model_dict["id"] == model.id
            assert model_dict["name"] == "E2E Test Model"
            assert model_dict["description"] == "Testing complete workflow"
            assert model_dict["value"] == 42
            assert "created_at" in model_dict
            assert "updated_at" in model_dict

            # 6. Проверяем метод __repr__
            repr_str = repr(model)
            assert "TestModel" in repr_str
            assert str(model.id) in repr_str

            # 7. Обновление модели
            original_updated_at = model.updated_at
            model.value = 100
            # В тестовой среде нужно явно обновить updated_at
            from datetime import datetime

            model.updated_at = datetime.now()
            session.commit()
            session.refresh(model)

            # 8. Проверяем что updated_at обновился
            assert model.updated_at > original_updated_at

            # 9. Проверяем обновленные данные
            updated_dict = model.to_dict()
            assert updated_dict["value"] == 100

            # 10. Удаление модели
            session.delete(model)
            session.commit()

            # 11. Проверяем что модель удалена
            deleted_model = session.get(TestModel, model.id)
            assert deleted_model is None

        finally:
            session.close()

    @pytest.mark.e2e
    def test_multiple_models_interaction(self, session_factory, base_class):
        """Тестирует взаимодействие нескольких моделей."""
        Base, TestModel = base_class
        session = session_factory()

        try:
            # Создаем несколько моделей
            models = []
            for i in range(3):
                model = TestModel(
                    name=f"Model {i}", description=f"Description {i}", value=i * 10
                )
                models.append(model)
                session.add(model)

            session.commit()

            # Проверяем что все модели созданы с уникальными id
            ids = [model.id for model in models]
            assert len(set(ids)) == 3
            assert all(id_val > 0 for id_val in ids)

            # Проверяем что все модели имеют временные метки
            for model in models:
                assert model.created_at is not None
                assert model.updated_at is not None

            # Проверяем методы всех моделей
            for i, model in enumerate(models):
                model_dict = model.to_dict()
                assert model_dict["name"] == f"Model {i}"
                assert model_dict["value"] == i * 10

            # Очищаем
            for model in models:
                session.delete(model)
            session.commit()

        finally:
            session.close()

    @pytest.mark.e2e
    def test_mixin_methods_under_load(self, session_factory, base_class):
        """Тестирует методы миксинов под нагрузкой."""
        Base, TestModel = base_class
        session = session_factory()

        try:
            # Создаем много моделей для тестирования производительности
            models = []
            for i in range(100):
                model = TestModel(
                    name=f"Load Test Model {i}",
                    description=f"Load test description {i}",
                    value=i,
                )
                models.append(model)
                session.add(model)

            session.commit()

            # Тестируем to_dict для всех моделей
            for model in models:
                model_dict = model.to_dict()
                assert (
                    len(model_dict) == 6
                )  # id, name, description, value, created_at, updated_at
                assert all(
                    key in model_dict for key in ["id", "name", "description", "value"]
                )

            # Тестируем __repr__ для всех моделей
            for model in models:
                repr_str = repr(model)
                assert "TestModel" in repr_str
                assert str(model.id) in repr_str

            # Очищаем
            for model in models:
                session.delete(model)
            session.commit()

        finally:
            session.close()
