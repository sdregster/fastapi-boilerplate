from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.dao.database import Base


class Role(Base):
    """Модель роли пользователя.

    Attributes:
        name: Название роли (уникальное).
    """

    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    def __repr__(self) -> str:
        """Возвращает строковое представление роли.

        Returns:
            str: Строковое представление роли.
        """
        return f"Role(id={self.id}, name={self.name})"


class User(Base):
    """Модель пользователя.

    Attributes:
        login: Логин пользователя.
        password: Хешированный пароль пользователя.
        role_id: ID роли пользователя.
        role: Связь с моделью роли.
    """

    login: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str]
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), default=1)
    role: Mapped["Role"] = relationship("Role")

    def __repr__(self) -> str:
        """Возвращает строковое представление пользователя.

        Returns:
            str: Строковое представление пользователя.
        """
        return f"User(id={self.id}, login={self.login})"
