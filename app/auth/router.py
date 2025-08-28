from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.auth.schemas import (
    SDynamicFilter,
    SUserAddDB,
    SUserAuth,
    SUserInfo,
    SUserRegister,
)
from app.auth.utils import authenticate_user
from app.dependencies.auth_dep import (
    get_current_admin_user,
    get_current_user,
    security_config,
)
from app.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import IncorrectEmailOrPasswordException, UserAlreadyExistsException
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Добавляем схему безопасности для Swagger UI
router.dependencies = [Depends(security_config)]


@router.post("/register/")
async def register_user(
    user_data: SUserRegister,
    session: AsyncSession = Depends(get_session_with_commit),
    current_admin: User = Depends(get_current_admin_user),
) -> dict:
    """Регистрирует нового пользователя.
    * только для администраторов и суперадминистраторов

    Args:
        user_data: Данные для регистрации пользователя.
        session: Сессия базы данных.
        current_admin: Текущий администратор, выполняющий регистрацию.

    Returns:
        dict: Сообщение об успешной регистрации.

    Raises:
        UserAlreadyExistsException: Если пользователь с таким логином уже существует.
    """
    # Проверка существования пользователя
    user_dao = UsersDAO(session)

    existing_user = await user_dao.find_one_or_none(
        filters=SDynamicFilter.create(login=user_data.login)
    )
    if existing_user:
        logger.warning(f"Попытка регистрации с существующим логином: {user_data.login}")
        raise UserAlreadyExistsException

    # Подготовка данных для добавления
    user_data_dict = user_data.model_dump()
    user_data_dict.pop("confirm_password", None)

    # Добавление пользователя
    await user_dao.add(values=SUserAddDB(**user_data_dict))
    return {"message": "Пользователь успешно зарегистрирован!"}


@router.post("/login/")
async def auth_user(
    user_data: SUserAuth,
    session: AsyncSession = Depends(get_session_without_commit),
) -> dict:
    """Аутентифицирует пользователя.

    Args:
        user_data: Данные для аутентификации.
        session: Сессия базы данных.

    Returns:
        dict: Сообщение об успешной авторизации.

    Raises:
        IncorrectEmailOrPasswordException: Если логин или пароль неверны.
    """
    logger.info(f"Попытка входа пользователя: {user_data.login}")

    users_dao = UsersDAO(session)
    user = await users_dao.find_one_or_none(
        filters=SDynamicFilter.create(login=user_data.login)
    )

    if not (user and await authenticate_user(user=user, password=user_data.password)):
        logger.warning(f"Неудачная попытка входа для пользователя: {user_data.login}")
        raise IncorrectEmailOrPasswordException

    logger.info(f"Пользователь успешно вошел в систему: {user_data.login}")
    return {"ok": True, "message": "Авторизация успешна!"}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    """Возвращает информацию о текущем пользователе.

    Args:
        user_data: Данные текущего пользователя.

    Returns:
        SUserInfo: Информация о пользователе.
    """
    logger.debug(f"Запрос информации о пользователе: {user_data.login}")
    return SUserInfo.model_validate(user_data)


@router.get("/all_users/")
async def get_all_users(
    session: AsyncSession = Depends(get_session_without_commit),
    user_data: User = Depends(get_current_admin_user),
) -> List[SUserInfo]:
    """Возвращает список всех пользователей.
    * только для администраторов и суперадминистраторов

    Args:
        session: Сессия базы данных.
        user_data: Данные администратора.

    Returns:
        List[SUserInfo]: Список всех пользователей.
    """
    logger.info(f"Администратор {user_data.login} запросил список всех пользователей")
    return await UsersDAO(session).find_all()
