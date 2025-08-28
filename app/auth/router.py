from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import RoleDAO, UsersDAO
from app.auth.models import User
from app.auth.schemas import (
    SDynamicFilter,
    SUserAuth,
    SUserCreateWithRole,
    SUserInfo,
    SUserRegister,
)
from app.auth.utils import authenticate_user
from app.dependencies.auth_dep import (
    get_current_admin_user,
    get_current_super_admin_user,
    get_current_user,
    security_config,
)
from app.dependencies.dao_dep import get_session_with_commit, get_session_without_commit
from app.exceptions import (
    ForbiddenException,
    IncorrectEmailOrPasswordException,
    UserAlreadyExistsException,
)
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
        filters=SDynamicFilter.create(login=user_data.login),
        load_relationships=["role"],
    )
    if existing_user:
        logger.warning(f"Попытка регистрации с существующим логином: {user_data.login}")
        raise UserAlreadyExistsException

    # Проверка прав на создание пользователя с указанной ролью
    from app.auth.enums import UserRole

    # Проверяем, что указанная роль существует в базе данных
    role_dao = RoleDAO(session)
    role = await role_dao.find_one_or_none_by_id(user_data.role_id)
    if not role:
        logger.warning(
            f"Попытка создания пользователя с несуществующей ролью: {user_data.role_id}"
        )
        raise ValueError("Указана несуществующая роль")

    # Администраторы могут создавать пользователей с ролями Guest и User
    # Суперадминистраторы могут создавать пользователей с любыми ролями
    if current_admin.role.id == UserRole.ADMIN:
        if user_data.role_id in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
            logger.warning(
                f"Администратор {current_admin.login} попытался создать пользователя "
                f"с ролью выше своей"
            )
            raise ForbiddenException(
                "Администраторы не могут создавать пользователей "
                "с ролями Admin или SuperAdmin"
            )

    # Суперадминистраторы могут создавать пользователей с любыми ролями
    elif current_admin.role.id == UserRole.SUPER_ADMIN:
        # Проверяем, что указанная роль находится в допустимом диапазоне
        if user_data.role_id not in [
            UserRole.GUEST,
            UserRole.USER,
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
        ]:
            logger.warning(
                f"Суперадминистратор {current_admin.login} попытался создать "
                f"пользователя с несуществующей ролью: {user_data.role_id}"
            )
            raise ValueError("Указана несуществующая роль")
    else:
        logger.warning(
            f"Пользователь {current_admin.login} с ролью {current_admin.role.name} "
            f"попытался зарегистрировать пользователя"
        )
        raise ForbiddenException("Недостаточно прав для регистрации пользователей")

    # Подготовка данных для добавления
    user_data_dict = user_data.model_dump()
    user_data_dict.pop("confirm_password", None)

    # Добавление пользователя с указанной ролью
    await user_dao.add(values=SUserCreateWithRole(**user_data_dict))
    return {"message": "Пользователь успешно зарегистрирован!"}


@router.get("/available_roles/")
async def get_available_roles(
    current_admin: User = Depends(get_current_admin_user),
) -> dict:
    """Возвращает список ролей, которые может назначать текущий администратор.

    Args:
        current_admin: Текущий администратор.

    Returns:
        dict: Список доступных ролей для назначения.
    """
    from app.auth.enums import UserRole

    if current_admin.role.id == UserRole.SUPER_ADMIN:
        # Суперадминистраторы могут назначать любые роли
        available_roles = [
            {
                "id": UserRole.GUEST,
                "name": "Гость",
                "description": "Базовая роль с минимальными правами",
            },
            {
                "id": UserRole.USER,
                "name": "Пользователь",
                "description": "Стандартная роль с базовыми правами",
            },
            {
                "id": UserRole.ADMIN,
                "name": "Администратор",
                "description": "Роль с расширенными правами управления",
            },
            {
                "id": UserRole.SUPER_ADMIN,
                "name": "Суперадминистратор",
                "description": "Роль с максимальными правами доступа",
            },
        ]
    elif current_admin.role.id == UserRole.ADMIN:
        # Администраторы могут назначать только роли Guest и User
        available_roles = [
            {
                "id": UserRole.GUEST,
                "name": "Гость",
                "description": "Базовая роль с минимальными правами",
            },
            {
                "id": UserRole.USER,
                "name": "Пользователь",
                "description": "Стандартная роль с базовыми правами",
            },
        ]
    else:
        available_roles = []

    return {
        "available_roles": available_roles,
        "current_admin_role": current_admin.role.name,
        "message": f"Доступные роли к созданию для {current_admin.role.name}",
    }


@router.get("/roles/")
async def get_all_roles(
    current_admin: User = Depends(get_current_admin_user),
) -> dict:
    """Возвращает список всех ролей в системе.

    Args:
        current_admin: Текущий администратор.

    Returns:
        dict: Список всех ролей с их описанием.
    """
    from app.auth.enums import UserRole

    all_roles = [
        {
            "id": UserRole.GUEST,
            "name": "Гость",
            "description": "Базовая роль с минимальными правами",
        },
        {
            "id": UserRole.USER,
            "name": "Пользователь",
            "description": "Стандартная роль с базовыми правами",
        },
        {
            "id": UserRole.ADMIN,
            "name": "Администратор",
            "description": "Роль с расширенными правами управления",
        },
        {
            "id": UserRole.SUPER_ADMIN,
            "name": "Суперадминистратор",
            "description": "Роль с максимальными правами доступа",
        },
    ]

    return {
        "roles": all_roles,
        "total_count": len(all_roles),
        "message": "Список всех ролей в системе",
    }


@router.put("/users/{user_id}/role/")
async def update_user_role(
    user_id: int,
    role_data: dict,
    session: AsyncSession = Depends(get_session_with_commit),
    current_admin: User = Depends(get_current_super_admin_user),
) -> dict:
    """Изменяет роль пользователя (только для суперадминистраторов).

    Args:
        user_id: ID пользователя для изменения роли.
        role_data: Данные с новой ролью {"role_id": int}.
        session: Сессия базы данных.
        current_admin: Текущий суперадминистратор.

    Returns:
        dict: Сообщение об успешном изменении роли.

    Raises:
        ValueError: Если указана несуществующая роль.
        ForbiddenException: Если у пользователя нет прав на изменение роли.
    """
    from app.auth.enums import UserRole

    new_role_id = role_data.get("role_id")
    if not new_role_id or new_role_id not in [
        UserRole.GUEST,
        UserRole.USER,
        UserRole.ADMIN,
        UserRole.SUPER_ADMIN,
    ]:
        raise ValueError("Указана недопустимая роль")

    # Проверяем, что указанная роль существует в базе данных
    role_dao = RoleDAO(session)
    role = await role_dao.find_one_or_none_by_id(new_role_id)
    if not role:
        raise ValueError("Указана несуществующая роль")

    # Получаем пользователя для изменения роли
    user_dao = UsersDAO(session)
    user = await user_dao.find_one_or_none_by_id(user_id)
    if not user:
        raise ValueError("Пользователь не найден")

    # Проверяем, что не пытаемся изменить роль суперадминистратора на более низкую
    if user.role.id == UserRole.SUPER_ADMIN and new_role_id != UserRole.SUPER_ADMIN:
        logger.warning(
            f"Суперадминистратор {current_admin.login} попытался понизить роль "
            f"другого суперадминистратора {user.login}"
        )
        raise ForbiddenException("Нельзя понизить роль суперадминистратора")

    # Обновляем роль пользователя
    from app.auth.schemas import SDynamicFilter

    await user_dao.update(
        filters=SDynamicFilter.create(id=user_id),
        values=type("RoleUpdate", (), {"role_id": new_role_id})(),
    )

    logger.info(
        f"Суперадминистратор {current_admin.login} изменил роль "
        f"пользователя {user.login} на {role.name}"
    )
    return {
        "message": f"Роль пользователя {user.login} успешно изменена на {role.name}",
        "user_id": user_id,
        "new_role": role.name,
        "changed_by": current_admin.login,
    }


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
        filters=SDynamicFilter.create(login=user_data.login),
        load_relationships=["role"],
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

    users = await UsersDAO(session).find_all(load_relationships=["role"])

    # Преобразуем SQLAlchemy модели в Pydantic схемы
    users_info = []
    for user in users:
        users_info.append(SUserInfo.model_validate(user))

    return users_info


@router.get("/system_info/")
async def get_system_info(
    session: AsyncSession = Depends(get_session_without_commit),
    user_data: User = Depends(get_current_super_admin_user),
) -> dict:
    """Получает системную информацию (только для суперадминистраторов).

    Args:
        session: Сессия базы данных.
        user_data: Данные суперадминистратора.

    Returns:
        dict: Системная информация о системе.

    Raises:
        ForbiddenException: Если у пользователя нет прав суперадминистратора.
    """
    logger.info(f"Суперадминистратор {user_data.login} запросил системную информацию")

    try:
        # Получаем статистику пользователей
        users_dao = UsersDAO(session)
        all_users = await users_dao.find_all(load_relationships=["role"])

        # Группируем пользователей по ролям
        role_stats = {}
        for user in all_users:
            role_name = user.role.name
            if role_name not in role_stats:
                role_stats[role_name] = 0
            role_stats[role_name] += 1

        # Получаем информацию о системе
        import os
        import platform
        from datetime import datetime

        import psutil

        system_info = {
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0],
                "processor": platform.processor(),
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "memory_available_gb": round(
                    psutil.virtual_memory().available / (1024**3), 2
                ),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage("/").percent
                if os.name != "nt"
                else "N/A",
            },
            "application": {
                "startup_time": datetime.now().isoformat(),
                "environment": os.getenv("APP_CONFIG__ENV", "development"),
                "debug_mode": os.getenv("APP_CONFIG__DEBUG", "false").lower() == "true",
            },
            "users": {
                "total_count": len(all_users),
                "by_role": role_stats,
                "last_activity": "N/A",  # Можно добавить отслеживание активности
            },
            "database": {
                "status": "connected",
                "session_count": "N/A",  # Можно добавить отслеживание сессий
            },
        }

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "requested_by": user_data.login,
            "data": system_info,
        }

    except Exception as e:
        logger.error(f"Ошибка при получении системной информации: {e}")
        return {
            "status": "error",
            "message": f"Ошибка при получении системной информации: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "requested_by": user_data.login,
        }
