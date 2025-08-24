import re
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.auth.utils import get_password_hash


class EmailModel(BaseModel):
    """Базовая модель с email полем.

    Attributes:
        email: Электронная почта пользователя.
    """

    email: EmailStr = Field(description="Электронная почта")
    model_config = ConfigDict(from_attributes=True)


class UserBase(EmailModel):
    """Базовая модель пользователя.

    Attributes:
        phone_number: Номер телефона в международном формате.
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
    """

    phone_number: str = Field(
        description="Номер телефона в международном формате, начинающийся с '+'"
    )
    first_name: str = Field(
        min_length=2, max_length=50, description="Имя, от 2 до 50 символов"
    )
    last_name: str = Field(
        min_length=2, max_length=50, description="Фамилия, от 2 до 50 символов"
    )

    @field_validator("phone_number")
    def validate_phone_number(cls, value: str) -> str:
        """Валидирует номер телефона.

        Args:
            value: Номер телефона для валидации.

        Returns:
            str: Валидный номер телефона.

        Raises:
            ValueError: Если номер телефона не соответствует формату.
        """
        if not re.match(r"^\+\d{5,15}$", value):
            raise ValueError(
                'Номер телефона должен начинаться с "+" и содержать от 5 до 15 цифр'
            )
        return value


class SUserRegister(UserBase):
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


class SUserAddDB(UserBase):
    """Схема добавления пользователя в базу данных.

    Attributes:
        password: Хешированный пароль пользователя.
    """

    password: str = Field(min_length=5, description="Пароль в формате HASH-строки")


class SUserAuth(EmailModel):
    """Схема аутентификации пользователя.

    Attributes:
        password: Пароль пользователя.
    """

    password: str = Field(
        min_length=4, max_length=50, description="Пароль, от 4 до 50 знаков"
    )


class RoleModel(BaseModel):
    """Модель роли.

    Attributes:
        id: Идентификатор роли.
        name: Название роли.
    """

    id: int = Field(description="Идентификатор роли")
    name: str = Field(description="Название роли")
    model_config = ConfigDict(from_attributes=True)


class SUserInfo(UserBase):
    """Схема информации о пользователе.

    Attributes:
        id: Идентификатор пользователя.
        role: Роль пользователя.
    """

    id: int = Field(description="Идентификатор пользователя")
    role: RoleModel = Field(exclude=True)

    @computed_field
    def role_name(self) -> str:
        """Возвращает название роли пользователя.

        Returns:
            str: Название роли.
        """
        return self.role.name

    @computed_field
    def role_id(self) -> int:
        """Возвращает ID роли пользователя.

        Returns:
            int: ID роли.
        """
        return self.role.id
