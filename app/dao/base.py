from typing import Generic, List, Type, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import func
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.schemas import SDynamicFilter

from .database import Base

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    """Базовый класс для работы с данными (Data Access Object).

    Attributes:
        model: Модель SQLAlchemy для работы с данными.
        _session: Сессия базы данных.
    """

    model: Type[T] = None

    def __init__(self, session: AsyncSession):
        """Инициализирует DAO с сессией базы данных.

        Args:
            session: Асинхронная сессия SQLAlchemy.

        Raises:
            ValueError: Если модель не указана в дочернем классе.
        """
        self._session = session
        if self.model is None:
            raise ValueError("Модель должна быть указана в дочернем классе")

    async def find_one_or_none_by_id(self, data_id: int):
        """Находит запись по ID.

        Args:
            data_id: ID записи для поиска.

        Returns:
            T | None: Найденная запись или None.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        try:
            query = select(self.model).filter_by(id=data_id)
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()
            status_msg = "найдена" if record else "не найдена"
            log_message = f"Запись {self.model.__name__} с ID {data_id} {status_msg}."
            logger.info(log_message)
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи с ID {data_id}: {e}")
            raise

    async def find_one_or_none(self, filters: "SDynamicFilter"):
        """Находит одну запись по фильтрам.

        Args:
            filters: SDynamicFilter с фильтрами для поиска.

        Returns:
            T | None: Найденная запись или None.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        filter_dict = filters.get_active_filters() if filters else {}
        logger.info(
            f"Поиск одной записи {self.model.__name__} по фильтрам: {filter_dict}"
        )
        try:
            query = select(self.model).filter_by(**filter_dict)
            result = await self._session.execute(query)
            record = result.scalar_one_or_none()
            status_msg = "найдена" if record else "не найдена"
            log_message = f"Запись {status_msg} по фильтрам: {filter_dict}"
            logger.info(log_message)
            return record
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при поиске записи по фильтрам {filter_dict}: {e}")
            raise

    async def find_all(self, filters: SDynamicFilter | None = None):
        """Находит все записи по фильтрам.

        Args:
            filters: SDynamicFilter с фильтрами для поиска (опционально).

        Returns:
            List[T]: Список найденных записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        filter_dict = filters.get_active_filters() if filters else {}
        logger.info(
            f"Поиск всех записей {self.model.__name__} по фильтрам: {filter_dict}"
        )
        try:
            query = select(self.model).filter_by(**filter_dict)
            result = await self._session.execute(query)
            records = result.scalars().all()
            logger.info(f"Найдено {len(records)} записей.")
            return records
        except SQLAlchemyError as e:
            logger.error(
                f"Ошибка при поиске всех записей по фильтрам {filter_dict}: {e}"
            )
            raise

    async def add(self, values: BaseModel):
        """Добавляет новую запись.

        Args:
            values: Pydantic модель с данными для добавления.

        Returns:
            T: Созданная запись.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(
            f"Добавление записи {self.model.__name__} с параметрами: {values_dict}"
        )
        try:
            new_instance = self.model(**values_dict)
            self._session.add(new_instance)
            logger.info(f"Запись {self.model.__name__} успешно добавлена.")
            await self._session.flush()
            return new_instance
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении записи: {e}")
            raise

    async def add_many(self, instances: List[BaseModel]):
        """Добавляет несколько записей.

        Args:
            instances: Список Pydantic моделей с данными для добавления.

        Returns:
            List[T]: Список созданных записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        values_list = [item.model_dump(exclude_unset=True) for item in instances]
        logger.info(
            f"Добавление нескольких записей {self.model.__name__}. "
            f"Количество: {len(values_list)}"
        )
        try:
            new_instances = [self.model(**values) for values in values_list]
            self._session.add_all(new_instances)
            logger.info(f"Успешно добавлено {len(new_instances)} записей.")
            await self._session.flush()
            return new_instances
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при добавлении нескольких записей: {e}")
            raise

    async def update(self, filters: SDynamicFilter, values: BaseModel):
        """Обновляет записи по фильтрам.

        Args:
            filters: SDynamicFilter с фильтрами для поиска записей.
            values: Pydantic модель с новыми данными.

        Returns:
            int: Количество обновленных записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        filter_dict = filters.get_active_filters()
        values_dict = values.model_dump(exclude_unset=True)
        logger.info(
            f"Обновление записей {self.model.__name__} по фильтру: {filter_dict} "
            f"с параметрами: {values_dict}"
        )
        try:
            query = (
                sqlalchemy_update(self.model)
                .where(*[getattr(self.model, k) == v for k, v in filter_dict.items()])
                .values(**values_dict)
                .execution_options(synchronize_session="fetch")
            )
            result = await self._session.execute(query)
            logger.info(f"Обновлено {result.rowcount} записей.")
            await self._session.flush()
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при обновлении записей: {e}")
            raise

    async def delete(self, filters: SDynamicFilter):
        """Удаляет записи по фильтрам.

        Args:
            filters: SDynamicFilter с фильтрами для поиска записей.

        Returns:
            int: Количество удаленных записей.

        Raises:
            ValueError: Если не указаны фильтры для удаления.
            SQLAlchemyError: При ошибке базы данных.
        """
        filter_dict = filters.get_active_filters()
        logger.info(f"Удаление записей {self.model.__name__} по фильтру: {filter_dict}")
        if not filter_dict:
            logger.error("Нужен хотя бы один фильтр для удаления.")
            raise ValueError("Нужен хотя бы один фильтр для удаления.")
        try:
            query = sqlalchemy_delete(self.model).filter_by(**filter_dict)
            result = await self._session.execute(query)
            logger.info(f"Удалено {result.rowcount} записей.")
            await self._session.flush()
            return result.rowcount
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении записей: {e}")
            raise

    async def count(self, filters: SDynamicFilter | None = None):
        """Подсчитывает количество записей по фильтрам.

        Args:
            filters: SDynamicFilter с фильтрами для поиска (опционально).

        Returns:
            int: Количество записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        filter_dict = filters.get_active_filters() if filters else {}
        logger.info(
            f"Подсчет количества записей {self.model.__name__} "
            f"по фильтру: {filter_dict}"
        )
        try:
            query = select(func.count(self.model.id)).filter_by(**filter_dict)
            result = await self._session.execute(query)
            count = result.scalar()
            logger.info(f"Найдено {count} записей.")
            return count
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при подсчете записей: {e}")
            raise

    async def bulk_update(self, records: List[BaseModel]):
        """Массово обновляет записи.

        Args:
            records: Список Pydantic моделей с данными для обновления.

        Returns:
            int: Количество обновленных записей.

        Raises:
            SQLAlchemyError: При ошибке базы данных.
        """
        logger.info(f"Массовое обновление записей {self.model.__name__}")
        try:
            updated_count = 0
            for record in records:
                record_dict = record.model_dump(exclude_unset=True)
                if "id" not in record_dict:
                    continue

                update_data = {k: v for k, v in record_dict.items() if k != "id"}
                stmt = (
                    sqlalchemy_update(self.model)
                    .filter_by(id=record_dict["id"])
                    .values(**update_data)
                )
                result = await self._session.execute(stmt)
                updated_count += result.rowcount

            logger.info(f"Обновлено {updated_count} записей")
            await self._session.flush()
            return updated_count
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при массовом обновлении: {e}")
            raise
