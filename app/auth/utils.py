from datetime import datetime, timedelta, timezone

from fastapi.responses import Response
from jose import jwt
from passlib.context import CryptContext

from app.config import settings


def create_tokens(data: dict) -> dict:
    """Создает access и refresh токены для пользователя.

    Args:
        data: Данные для включения в токен.

    Returns:
        dict: Словарь с access и refresh токенами.
    """
    # Текущее время в UTC
    now = datetime.now(timezone.utc)

    # AccessToken - 30 минут
    access_expire = now + timedelta(seconds=10)
    access_payload = data.copy()
    access_payload.update({"exp": int(access_expire.timestamp()), "type": "access"})
    access_token = jwt.encode(
        access_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    # RefreshToken - 7 дней
    refresh_expire = now + timedelta(days=7)
    refresh_payload = data.copy()
    refresh_payload.update({"exp": int(refresh_expire.timestamp()), "type": "refresh"})
    refresh_token = jwt.encode(
        refresh_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
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


def set_tokens(response: Response, user_id: int):
    """Устанавливает токены в cookies ответа.

    Args:
        response: HTTP ответ для установки cookies.
        user_id: ID пользователя для создания токенов.
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
