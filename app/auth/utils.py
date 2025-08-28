import base64
from typing import TYPE_CHECKING, Optional, Tuple

from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.utils import get_logger

if TYPE_CHECKING:
    from app.auth.models import User

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def decode_basic_auth(authorization_header: str) -> Tuple[str, str]:
    """Декодирует заголовок Basic Auth и возвращает username и password.

    Args:
        authorization_header: Заголовок Authorization в формате "Basic base64".

    Returns:
        Tuple[str, str]: Кортеж (username, password).

    Raises:
        HTTPException: Если заголовок некорректен или не содержит Basic Auth.
    """
    try:
        if not authorization_header.startswith("Basic "):
            logger.warning(
                "Попытка аутентификации с некорректным заголовком Authorization"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется Basic аутентификация",
                headers={"WWW-Authenticate": "Basic"},
            )

        # Убираем "Basic " и декодируем base64
        encoded_credentials = authorization_header[6:]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")

        # Разделяем username:password
        if ":" not in decoded_credentials:
            logger.warning(
                "Попытка аутентификации с некорректным форматом учетных данных"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Некорректный формат учетных данных",
                headers={"WWW-Authenticate": "Basic"},
            )

        username, password = decoded_credentials.split(":", 1)
        logger.debug(f"Попытка аутентификации для пользователя: {username}")
        return username, password

    except (base64.binascii.Error, UnicodeDecodeError):
        logger.error("Ошибка декодирования Basic Auth заголовка")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректно закодированные учетные данные",
            headers={"WWW-Authenticate": "Basic"},
        )


async def authenticate_user(user, password: str) -> Optional["User"]:
    """Аутентифицирует пользователя по паролю.

    Args:
        user: Объект пользователя.
        password: Пароль для проверки.

    Returns:
        User | None: Пользователь при успешной аутентификации, None в противном случае
    """
    if not user:
        logger.warning("Попытка аутентификации несуществующего пользователя")
        return None

    # Проверяем пароль
    if not verify_password(plain_password=password, hashed_password=user.password):
        user_login = getattr(user, "login", "unknown")
        logger.warning(
            f"Неудачная попытка аутентификации для пользователя: {user_login}"
        )
        return None

    logger.info(
        f"Успешная аутентификация пользователя: {getattr(user, 'login', 'unknown')}"
    )
    return user


def get_password_hash(password: str) -> str:
    """Хеширует пароль пользователя.

    Args:
        password: Пароль в открытом виде.

    Returns:
        str: Хешированный пароль.
    """
    logger.debug("Хеширование пароля пользователя")
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
