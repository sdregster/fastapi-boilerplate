from app.auth.models import Role, User
from app.dao.base import BaseDAO


class UsersDAO(BaseDAO):
    """DAO для работы с пользователями.

    Attributes:
        model: Модель пользователя.
    """

    model = User


class RoleDAO(BaseDAO):
    """DAO для работы с ролями.

    Attributes:
        model: Модель роли.
    """

    model = Role
