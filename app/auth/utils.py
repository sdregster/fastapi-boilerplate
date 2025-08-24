from datetime import datetime, timedelta, timezone

from fastapi.responses import Response
from jose import jwt
from passlib.context import CryptContext

from app.config import settings


def create_tokens(data: dict) -> dict:
    """Создает access и refresh токены для пользователя с конфигурируемыми настройками.

    Функция создает два типа JWT токенов:
    - Access токен: используется для доступа к защищенным ресурсам
    - Refresh токен: используется для обновления access токенов

    Время жизни токенов и дополнительные поля безопасности настраиваются
    через переменные окружения в settings.jwt.

    Добавляемые поля в токен:
    - exp: время истечения токена (timestamp)
    - type: тип токена ('access' или 'refresh')
    - iat: время создания токена (timestamp)
    - iss: издатель токена (из настроек)
    - aud: аудитория токена (из настроек)

    Args:
        data: Данные пользователя для включения в токен (обычно {'sub': user_id}).

    Returns:
        dict: Словарь с ключами 'access_token' и 'refresh_token',
              содержащими подписанные JWT строки.

    Example:
        >>> tokens = create_tokens({"sub": "123"})
        >>> print(tokens)
        {'access_token': 'eyJ...', 'refresh_token': 'eyJ...'}
    """
    # Текущее время в UTC
    now = datetime.now(timezone.utc)

    # AccessToken - настраиваемое время жизни
    access_expire = now + timedelta(minutes=settings.jwt.access_token_expire_minutes)
    access_payload = data.copy()
    access_payload.update(
        {
            "exp": int(access_expire.timestamp()),
            "type": "access",
            "iat": int(now.timestamp()),  # Время создания токена
            "iss": settings.jwt.issuer,  # Издатель токена
            "aud": settings.jwt.audience,  # Аудитория токена
        }
    )
    access_token = jwt.encode(
        access_payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )

    # RefreshToken - настраиваемое время жизни
    refresh_expire = now + timedelta(days=settings.jwt.refresh_token_expire_days)
    refresh_payload = data.copy()
    refresh_payload.update(
        {
            "exp": int(refresh_expire.timestamp()),
            "type": "refresh",
            "iat": int(now.timestamp()),  # Время создания токена
            "iss": settings.jwt.issuer,  # Издатель токена
            "aud": settings.jwt.audience,  # Аудитория токена
        }
    )
    refresh_token = jwt.encode(
        refresh_payload, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )

    return {"access_token": access_token, "refresh_token": refresh_token}


async def authenticate_user(user, password):
    """Аутентифицирует пользователя по паролю.

    Args:
        user: Объект пользователя.
        password: Пароль для проверки.

    Returns:
        User | None: Пользователь при успешной аутентификации, None в противном случае.
    """
    if (
        not user
        or verify_password(plain_password=password, hashed_password=user.password)
        is False
    ):
        return None
    return user


def set_tokens(response: Response, user_id: int) -> None:
    """Устанавливает JWT токены в HTTP cookies с безопасными настройками.

    Создает access и refresh токены для указанного пользователя и устанавливает
    их в HTTP cookies с защищенными настройками:
    - httponly=True: защита от XSS атак
    - secure=True: передача только по HTTPS
    - samesite="lax": защита от CSRF атак

    Args:
        response: HTTP ответ FastAPI для установки cookies.
        user_id: Идентификатор пользователя для создания токенов.

    Returns:
        None: Функция изменяет response объект напрямую.

    Note:
        Cookies устанавливаются с ключами:
        - 'user_access_token': для access токена
        - 'user_refresh_token': для refresh токена
    """
    new_tokens = create_tokens(data={"sub": str(user_id)})
    access_token = new_tokens.get("access_token")
    refresh_token = new_tokens.get("refresh_token")

    response.set_cookie(
        key="user_access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )

    response.set_cookie(
        key="user_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
    )


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Хеширует пароль пользователя.

    Args:
        password: Пароль в открытом виде.

    Returns:
        str: Хешированный пароль.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хешу.

    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Хешированный пароль.

    Returns:
        bool: True если пароли совпадают, False в противном случае.
    """
    return pwd_context.verify(plain_password, hashed_password)
