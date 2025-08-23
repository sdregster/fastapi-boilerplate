from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.database import async_session_maker


async def get_session_with_commit() -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет асинхронную сессию с автоматическим коммитом.

    Yields:
        AsyncSession: Сессия базы данных.

    Note:
        Автоматически коммитит изменения при успешном завершении
        и откатывает при возникновении ошибки.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_session_without_commit() -> AsyncGenerator[AsyncSession, None]:
    """Предоставляет асинхронную сессию без автоматического коммита.

    Yields:
        AsyncSession: Сессия базы данных.

    Note:
        Не коммитит изменения автоматически, только откатывает при ошибке.
        Полезно для операций чтения или когда коммит нужен вручную.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
