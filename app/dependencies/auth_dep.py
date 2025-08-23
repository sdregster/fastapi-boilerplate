from datetime import datetime, timezone

from fastapi import Depends, Request
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.config import settings
from app.dependencies.dao_dep import get_session_without_commit
from app.exceptions import (
    ForbiddenException,
    NoJwtException,
    NoUserIdException,
    TokenExpiredException,
    TokenNoFound,
    UserNotFoundException,
)


def get_access_token(request: Request) -> str:
    """Извлекает access_token из cookies.

    Args:
        request: HTTP запрос для извлечения cookies.

    Returns:
        str: Access токен.

    Raises:
        TokenNoFound: Если токен не найден в cookies.
    """
    token = request.cookies.get("user_access_token")
    if not token:
        raise TokenNoFound
    return token


def get_refresh_token(request: Request) -> str:
    """Извлекает refresh_token из cookies.

    Args:
        request: HTTP запрос для извлечения cookies.

    Returns:
        str: Refresh токен.

    Raises:
        TokenNoFound: Если токен не найден в cookies.
    """
    token = request.cookies.get("user_refresh_token")
    if not token:
        raise TokenNoFound
    return token


async def check_refresh_token(
    token: str = Depends(get_refresh_token),
    session: AsyncSession = Depends(get_session_without_commit),
) -> User:
    """Проверяет refresh_token и возвращает пользователя.

    Args:
        token: Refresh токен для проверки.
        session: Сессия базы данных.

    Returns:
        User: Пользователь, связанный с токеном.

    Raises:
        NoJwtException: Если токен недействителен или пользователь не найден.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise NoJwtException

        user = await UsersDAO(session).find_one_or_none_by_id(data_id=int(user_id))
        if not user:
            raise NoJwtException

        return user
    except JWTError:
        raise NoJwtException


async def get_current_user(
    token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session_without_commit),
) -> User:
    """Проверяет access_token и возвращает пользователя.

    Args:
        token: Access токен для проверки.
        session: Сессия базы данных.

    Returns:
        User: Текущий пользователь.

    Raises:
        TokenExpiredException: Если токен истек.
        NoJwtException: Если токен недействителен.
        NoUserIdException: Если ID пользователя отсутствует в токене.
        UserNotFoundException: Если пользователь не найден.
    """
    try:
        # Декодируем токен
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except ExpiredSignatureError:
        raise TokenExpiredException
    except JWTError:
        # Общая ошибка для токенов
        raise NoJwtException

    expire: str = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise TokenExpiredException

    user_id: str = payload.get("sub")
    if not user_id:
        raise NoUserIdException

    user = await UsersDAO(session).find_one_or_none_by_id(data_id=int(user_id))
    if not user:
        raise UserNotFoundException
    return user


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
