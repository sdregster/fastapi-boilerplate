from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.database import Base


class Role(Base):
    """Модель роли пользователя.

    Attributes:
        name: Название роли (уникальное).
        users: Список пользователей с данной ролью.
    """

    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        """Возвращает строковое представление роли.

        Returns:
            str: Строковое представление роли.
        """
        return f"{self.__class__.__name__}(id={self.id}, name={self.name})"


class User(Base):
    """Модель пользователя.

    Attributes:
        phone_number: Номер телефона пользователя (уникальный).
        first_name: Имя пользователя.
        last_name: Фамилия пользователя.
        email: Email пользователя (уникальный).
        password: Хешированный пароль пользователя.
        role_id: ID роли пользователя.
        role: Связь с моделью роли.
    """

    phone_number: Mapped[str] = mapped_column(unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str]
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), default=1, server_default=text("1")
    )
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")

    def __repr__(self) -> str:
        """Возвращает строковое представление пользователя.

        Returns:
            str: Строковое представление пользователя.
        """
        return f"{self.__class__.__name__}(id={self.id})"
