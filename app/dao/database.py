from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.config import NAMING_CONVENTION, database_url
from app.dao.mixins import BaseMixin, IdMixin, TimestampMixin
from app.utils import camel_case_to_snake_case

engine = create_async_engine(url=database_url)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(AsyncAttrs, DeclarativeBase, IdMixin, TimestampMixin, BaseMixin):
    """Базовый класс для всех моделей базы данных.

    Attributes:
        metadata: Метаданные с соглашениями по именованию.
    """

    __abstract__ = True

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr
    def __tablename__(cls) -> str:
        """Автоматически генерирует имя таблицы на основе имени класса.

        Returns:
            str: Имя таблицы в snake_case с множественным числом.
        """
        return f"{camel_case_to_snake_case(cls.__name__)}s"
