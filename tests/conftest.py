"""Конфигурация pytest для тестов FastAPI бойлерплейта."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.dao.mixins.base_mixin import BaseMixin
from app.dao.mixins.id_mixin import IdMixin
from app.dao.mixins.timestamp_mixin import TimestampMixin

# Глобальные фикстуры для всех типов тестов


@pytest.fixture(scope="session")
def engine():
    """Создает тестовый движок базы данных в памяти."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="function")
def db_session(engine):
    """Создает тестовую сессию базы данных."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Создаем таблицы для тестов
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    # Создаем тестовую модель с миксинами
    class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
        __tablename__ = "test_model"

    Base.metadata.create_all(bind=engine)

    yield session

    session.close()


@pytest.fixture
def db(db_session):
    """Фикстура для внедрения тестовой базы данных."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    return override_get_db


@pytest.fixture
def test_model_class():
    """Возвращает класс тестовой модели с миксинами."""
    from sqlalchemy import Column, String
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()

    class TestModel(Base, IdMixin, TimestampMixin, BaseMixin):
        __tablename__ = "test_model"
        name = Column(String(50))

    return TestModel
