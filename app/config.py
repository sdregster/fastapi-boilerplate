import os

from pydantic_settings import BaseSettings, SettingsConfigDict

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных среды.

    Attributes:
        BASE_DIR: Базовая директория проекта.
        DB_URL: URL для подключения к базе данных.
        SECRET_KEY: Секретный ключ для JWT токенов.
        ALGORITHM: Алгоритм шифрования для JWT токенов.
    """

    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    DB_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/db.sqlite3"
    SECRET_KEY: str
    ALGORITHM: str

    model_config = SettingsConfigDict(env_file=f"{BASE_DIR}/.env")


# Получаем параметры для загрузки переменных среды
settings = Settings()
database_url = settings.DB_URL
