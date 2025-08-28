"""Константы для модуля авторизации."""

from app.auth.enums import UserRole

# Сообщения об ошибках аутентификации
AUTH_REQUIRED_MESSAGE = "Требуется аутентификация"
INVALID_CREDENTIALS_MESSAGE = "Неверные учетные данные"
AUTH_ERROR_MESSAGE = "Ошибка аутентификации"

# Сообщения для ролей
ROLE_NAMES = {
    UserRole.GUEST: "Гость",
    UserRole.USER: "Пользователь",
    UserRole.ADMIN: "Администратор",
    UserRole.SUPER_ADMIN: "Суперадминистратор",
}

# Описания ролей
ROLE_DESCRIPTIONS = {
    UserRole.GUEST: "Базовая роль с минимальными правами",
    UserRole.USER: "Стандартная роль с базовыми правами",
    UserRole.ADMIN: "Роль с расширенными правами управления",
    UserRole.SUPER_ADMIN: "Роль с максимальными правами доступа",
}

# Права доступа по ролям
ROLE_PERMISSIONS = {
    UserRole.GUEST: ["read_public"],
    UserRole.USER: ["read_public", "read_own", "write_own"],
    UserRole.ADMIN: [
        "read_public",
        "read_own",
        "write_own",
        "manage_users",
        "read_all",
    ],
    UserRole.SUPER_ADMIN: [
        "read_public",
        "read_own",
        "write_own",
        "manage_users",
        "read_all",
        "system_access",
        "manage_roles",
    ],
}
