from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.auth.utils import decode_basic_auth
from app.dependencies.dao_dep import get_session_without_commit
from app.exceptions import (
    ForbiddenException,
)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session_without_commit),
) -> User:
    """Проверяет Basic Auth и возвращает текущего пользователя.

    Выполняет проверку заголовка Authorization с Basic Auth:
    - Декодирует base64(username:password)
    - Проверяет учетные данные пользователя
    - Возвращает объект пользователя из базы данных

    Функция используется как dependency для защищенных эндпоинтов API.

    Args:
        request: HTTP запрос для извлечения заголовка Authorization.
        session: Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        User: Объект текущего аутентифицированного пользователя.

    Raises:
        HTTPException: При ошибках аутентификации (401 Unauthorized).
        UserNotFoundException: Если пользователь не найден в базе данных.
    """
    authorization_header = request.headers.get("Authorization")
    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        username, password = decode_basic_auth(authorization_header)

        # Ищем пользователя по email (username)
        user_dao = UsersDAO(session)
        user = await user_dao.find_one_or_none(filters={"email": username})

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные",
                headers={"WWW-Authenticate": "Basic"},
            )

        # Проверяем пароль
        from app.auth.utils import authenticate_user

        authenticated_user = await authenticate_user(user, password)

        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные",
                headers={"WWW-Authenticate": "Basic"},
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ошибка аутентификации",
            headers={"WWW-Authenticate": "Basic"},
        )


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверяет права пользователя как администратора.

    Args:
        current_user: Текущий пользователь для проверки прав.

    Returns:
        User: Пользователь с правами администратора.

    Raises:
        ForbiddenException: Если у пользователя нет прав администратора.
    """
    if current_user.role.id in [3, 4]:
        return current_user
    raise ForbiddenException
