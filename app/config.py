from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class JwtConfig(BaseModel):
    """Конфигурация для JWT токенов с расширенными настройками безопасности.

    Класс содержит все настройки для создания и валидации JWT токенов,
    включая время жизни, алгоритмы подписи и дополнительные поля безопасности.
    """

    secret_key: str  # Секретный ключ для подписи токенов (обязательно из .env)
    algorithm: str = "HS256"  # Алгоритм подписи (рекомендуется HS256)

    # Настройки времени жизни токенов
    access_token_expire_minutes: int = 30  # Время жизни access токена в минутах
    refresh_token_expire_days: int = 7  # Время жизни refresh токена в днях

    # Дополнительные настройки безопасности (JWT claims)
    token_type: str = "Bearer"  # Тип токена для Authorization заголовка
    issuer: str = "fastapi-auth-app"  # Издатель токена (iss claim)
    audience: str = "fastapi-auth-users"  # Аудитория токена (aud claim)


class Settings(BaseSettings):
    """Основные настройки приложения, загружаемые из переменных среды.

    Класс использует Pydantic Settings для автоматической загрузки конфигурации
    из файлов .env и переменных окружения с поддержкой вложенной структуры.

    Attributes:
        run: Настройки запуска приложения (хост, порт).
        db: Конфигурация базы данных (URL, пулы соединений).
        jwt: Настройки JWT токенов (ключи, время жизни, безопасность).

    Environment Variables:
        Используется префикс APP_CONFIG__ и разделитель __ для вложенности:
        - APP_CONFIG__DB__URL: URL базы данных
        - APP_CONFIG__JWT__SECRET_KEY: секретный ключ для JWT
        - APP_CONFIG__JWT__ACCESS_TOKEN_EXPIRE_MINUTES: время жизни access токена
        и т.д.

    Config Files:
        Загружает настройки из файлов в порядке приоритета:
        1. .env (высший приоритет)
        2. .env.template (резервный файл)
    """

    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    run: RunConfig = RunConfig()
    db: DatabaseConfig
    jwt: JwtConfig


settings = Settings()
