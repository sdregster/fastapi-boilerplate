from typing import Any, Dict, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.auth.utils import get_password_hash


class UserModel(BaseModel):
    """Базовая модель пользователя.

    Attributes:
        login: Логин пользователя.
    """

    login: str = Field(
        min_length=3, max_length=50, description="Логин, от 3 до 50 символов"
    )
    model_config = ConfigDict(from_attributes=True)


class SUserRegister(UserModel):
    """Схема регистрации пользователя.

    Attributes:
        password: Пароль пользователя.
        confirm_password: Подтверждение пароля.
    """

    password: str = Field(
        min_length=4, max_length=50, description="Пароль, от 4 до 50 знаков"
    )
    confirm_password: str = Field(
        min_length=4, max_length=50, description="Повторите пароль"
    )

    @model_validator(mode="after")
    def check_password(self) -> Self:
        """Проверяет совпадение паролей и хеширует пароль.

        Returns:
            Self: Экземпляр модели с хешированным паролем.

        Raises:
            ValueError: Если пароли не совпадают.
        """
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")
        self.password = get_password_hash(
            self.password
        )  # хешируем пароль до сохранения в базе данных
        return self


class SUserAddDB(UserModel):
    """Схема добавления пользователя в базу данных.

    Attributes:
        password: Хешированный пароль пользователя.
    """

    password: str = Field(min_length=5, description="Пароль в формате HASH-строки")


class SUserCreateWithRole(UserModel):
    """Схема создания пользователя с указанием роли.

    Attributes:
        password: Хешированный пароль пользователя.
        role_id: ID роли пользователя.
    """

    password: str = Field(min_length=5, description="Пароль в формате HASH-строки")
    role_id: int = Field(description="ID роли пользователя")


class SDynamicFilter(BaseModel):
    """Универсальная схема фильтрации для любых моделей.

    Attributes:
        filters: Словарь фильтров в формате {поле: значение}.
                 Поддерживает None значения для игнорирования поля.
    """

    filters: Dict[str, Any] = Field(
        default_factory=dict, description="Фильтры в формате {поле: значение}"
    )

    @classmethod
    def create(cls, **kwargs) -> "SDynamicFilter":
        """Создает фильтр из именованных аргументов.

        Args:
            **kwargs: Поля фильтрации в виде именованных аргументов.

        Returns:
            SDynamicFilter: Новый экземпляр фильтра.

        Examples:
            >>> SDynamicFilter.create(login="admin", role_id=1)
            >>> SDynamicFilter.create(name="SuperAdmin")
        """
        return cls(filters=kwargs)

    def get_active_filters(self) -> Dict[str, Any]:
        """Возвращает только активные фильтры (без None значений).

        Returns:
            Dict[str, Any]: Словарь активных фильтров.
        """
        return {k: v for k, v in self.filters.items() if v is not None}


class SUserAuth(UserModel):
    """Схема аутентификации пользователя.

    Attributes:
        password: Пароль пользователя.
    """

    password: str = Field(
        min_length=4, max_length=50, description="Пароль, от 4 до 50 знаков"
    )


class SRoleModel(BaseModel):
    """Модель роли.

    Attributes:
        id: Идентификатор роли.
        name: Название роли.
    """

    id: int = Field(description="Идентификатор роли")
    name: str = Field(description="Название роли")
    model_config = ConfigDict(from_attributes=True)


class SRoleCreate(BaseModel):
    """Схема создания роли.

    Attributes:
        name: Название роли.
    """

    name: str = Field(description="Название роли")


class SUserInfo(UserModel):
    """Схема информации о пользователе.

    Attributes:
        id: Идентификатор пользователя.
        role: Роль пользователя.
    """

    id: int = Field(description="Идентификатор пользователя")
    role: SRoleModel = Field(exclude=True)

    @property
    def role_name(self) -> str:
        """Возвращает название роли пользователя.

        Returns:
            str: Название роли.
        """
        return self.role.name

    @property
    def role_id(self) -> int:
        """Возвращает ID роли пользователя.

        Returns:
            int: ID роли.
        """
        return self.role.id
