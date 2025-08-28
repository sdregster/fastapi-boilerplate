from enum import IntEnum


class UserRole(IntEnum):
    """Enum для ролей пользователей.

    Attributes:
        GUEST: Гость (базовая роль, минимальные права)
        USER: Обычный пользователь (стандартные права)
        ADMIN: Администратор (расширенные права)
        SUPER_ADMIN: Суперадминистратор (максимальные права)
    """

    GUEST = 1
    USER = 2
    ADMIN = 3
    SUPER_ADMIN = 4

    @classmethod
    def get_admin_roles(cls) -> list["UserRole"]:
        """Возвращает роли с правами администратора.

        Returns:
            list[UserRole]: Список ролей администраторов.
        """
        return [cls.ADMIN, cls.SUPER_ADMIN]

    @classmethod
    def is_admin(cls, role_id: int) -> bool:
        """Проверяет, является ли роль административной.

        Args:
            role_id: ID роли для проверки.

        Returns:
            bool: True если роль административная, False в противном случае.
        """
        return role_id in [cls.ADMIN, cls.SUPER_ADMIN]

    @classmethod
    def get_name(cls, role_id: int) -> str:
        """Возвращает название роли по ID.

        Args:
            role_id: ID роли.

        Returns:
            str: Название роли.
        """
        try:
            return cls(role_id).name
        except ValueError:
            return f"Unknown Role ({role_id})"
