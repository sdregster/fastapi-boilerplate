from typing import List

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UsersDAO
from app.auth.models import User
from app.auth.schemas import EmailModel, SUserAddDB, SUserAuth, SUserInfo, SUserRegister
from app.auth.utils import authenticate_user, set_tokens
from app.dependencies.auth_dep import (
    check_refresh_token,
    get_current_admin_user,
    get_current_user,
)
from app.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import IncorrectEmailOrPasswordException, UserAlreadyExistsException

router = APIRouter()


@router.post("/register/")
async def register_user(
    user_data: SUserRegister, session: AsyncSession = Depends(get_session_with_commit)
) -> dict:
    """Регистрирует нового пользователя.

    Args:
        user_data: Данные для регистрации пользователя.
        session: Сессия базы данных.

    Returns:
        dict: Сообщение об успешной регистрации.

    Raises:
        UserAlreadyExistsException: Если пользователь с таким email уже существует.
    """
    # Проверка существования пользователя
    user_dao = UsersDAO(session)

    existing_user = await user_dao.find_one_or_none(
        filters=EmailModel(email=user_data.email)
    )
    if existing_user:
        raise UserAlreadyExistsException

    # Подготовка данных для добавления
    user_data_dict = user_data.model_dump()
    user_data_dict.pop("confirm_password", None)

    # Добавление пользователя
    await user_dao.add(values=SUserAddDB(**user_data_dict))

    return {"message": "Вы успешно зарегистрированы!"}


@router.post("/login/")
async def auth_user(
    response: Response,
    user_data: SUserAuth,
    session: AsyncSession = Depends(get_session_without_commit),
) -> dict:
    """Аутентифицирует пользователя и устанавливает токены.

    Args:
        response: HTTP ответ для установки cookies.
        user_data: Данные для аутентификации.
        session: Сессия базы данных.

    Returns:
        dict: Сообщение об успешной авторизации.

    Raises:
        IncorrectEmailOrPasswordException: Если email или пароль неверны.
    """
    users_dao = UsersDAO(session)
    user = await users_dao.find_one_or_none(filters=EmailModel(email=user_data.email))

    if not (user and await authenticate_user(user=user, password=user_data.password)):
        raise IncorrectEmailOrPasswordException
    set_tokens(response, user.id)
    return {"ok": True, "message": "Авторизация успешна!"}


@router.post("/logout")
async def logout(response: Response):
    """Выход пользователя из системы.

    Args:
        response: HTTP ответ для удаления cookies.

    Returns:
        dict: Сообщение об успешном выходе.
    """
    response.delete_cookie("user_access_token")
    response.delete_cookie("user_refresh_token")
    return {"message": "Пользователь успешно вышел из системы"}


@router.get("/me/")
async def get_me(user_data: User = Depends(get_current_user)) -> SUserInfo:
    """Возвращает информацию о текущем пользователе.

    Args:
        user_data: Данные текущего пользователя.

    Returns:
        SUserInfo: Информация о пользователе.
    """
    return SUserInfo.model_validate(user_data)


@router.get("/all_users/")
async def get_all_users(
    session: AsyncSession = Depends(get_session_with_commit),
    user_data: User = Depends(get_current_admin_user),
) -> List[SUserInfo]:
    """Возвращает список всех пользователей (только для администраторов).

    Args:
        session: Сессия базы данных.
        user_data: Данные администратора.

    Returns:
        List[SUserInfo]: Список всех пользователей.
    """
    return await UsersDAO(session).find_all()


@router.post("/refresh")
async def process_refresh_token(
    response: Response, user: User = Depends(check_refresh_token)
):
    """Обновляет токены пользователя.

    Args:
        response: HTTP ответ для установки новых cookies.
        user: Пользователь, чьи токены обновляются.

    Returns:
        dict: Сообщение об успешном обновлении токенов.
    """
    set_tokens(response, user.id)
    return {"message": "Токены успешно обновлены"}
