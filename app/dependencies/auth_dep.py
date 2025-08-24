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
    """Проверяет refresh_token и возвращает пользователя с расширенной валидацией.

    Выполняет полную валидацию refresh токена включая:
    - Проверку подписи с помощью секретного ключа
    - Валидацию алгоритма подписи
    - Проверку издателя (issuer) токена
    - Проверку аудитории (audience) токена
    - Проверку существования пользователя в базе данных

    Args:
        token: Refresh токен, извлеченный из HTTP cookies.
        session: Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        User: Объект пользователя из базы данных, связанный с токеном.

    Raises:
        NoJwtException: При любых ошибках валидации токена или если
                       пользователь не найден в базе данных.

    Note:
        Использует настройки из settings.jwt для проверки токена.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,  # Проверяем аудиторию
            issuer=settings.jwt.issuer,  # Проверяем издателя
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
    """Проверяет access_token и возвращает текущего пользователя с полной валидацией.

    Выполняет комплексную проверку access токена:
    - Декодирование с проверкой подписи, алгоритма, издателя и аудитории
    - Проверку времени истечения токена (exp claim)
    - Извлечение и валидацию ID пользователя (sub claim)
    - Поиск пользователя в базе данных

    Функция используется как dependency для защищенных эндпоинтов API.

    Args:
        token: Access токен, извлеченный из HTTP cookies.
        session: Асинхронная сессия SQLAlchemy для работы с БД.

    Returns:
        User: Объект текущего аутентифицированного пользователя.

    Raises:
        TokenExpiredException: Если токен истек (проверяется дважды -
                              автоматически при декодировании и вручную).
        NoJwtException: При ошибках валидации токена (неверная подпись,
                       алгоритм, издатель, аудитория).
        NoUserIdException: Если в токене отсутствует ID пользователя (sub claim).
        UserNotFoundException: Если пользователь не найден в базе данных.

    Note:
        Использует конфигурацию из settings.jwt для всех проверок безопасности.
    """
    try:
        # Декодируем токен с дополнительными проверками
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,  # Проверяем аудиторию
            issuer=settings.jwt.issuer,  # Проверяем издателя
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
