from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    """Настройки запуска приложения.

    Attributes:
        host: Хост для запуска приложения.
        port: Порт для запуска приложения.
    """

    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseConfig(BaseModel):
    """Конфигурация базы данных.

    Attributes:
        url: URL подключения к базе данных.
        echo: Включение/выключение SQL логирования.
        echo_pool: Включение/выключение логирования пула соединений.
        pool_size: Размер пула соединений.
        max_overflow: Максимальное количество дополнительных соединений.
        naming_convention: Конвенции именования для базы данных.
    """

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


class SuperAdminConfig(BaseModel):
    """Конфигурация суперадминистратора.

    Attributes:
        login: Логин суперадминистратора.
        password: Пароль суперадминистратора.
    """

    login: str
    password: str


class LoggingConfig(BaseModel):
    """Конфигурация для логирования приложения.

    Attributes:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: Формат сообщений логов.
        directory: Папка для хранения логов.
        max_size: Максимальный размер файла лога в мегабайтах.
        backup_count: Количество файлов бэкапа для ротации логов.
        console_output: Включение/выключение вывода логов в консоль.
        file_output: Включение/выключение записи логов в файлы.
    """

    level: str = "INFO"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    directory: str = "logs"
    max_size: int = 10  # MB
    backup_count: int = 5
    console_output: bool = True
    file_output: bool = True


class Settings(BaseSettings):
    """Основные настройки приложения, загружаемые из переменных среды.

    Класс использует Pydantic Settings для автоматической загрузки конфигурации
    из файлов .env и переменных окружения с поддержкой вложенной структуры.

    Attributes:
        run: Настройки запуска приложения (хост, порт).
        db: Конфигурация базы данных (URL, пулы соединений).
        logging: Настройки логирования (уровень, формат, папка).
        superadmin: Конфигурация суперадминистратора (логин, пароль).

    Environment Variables:
        Используется префикс APP_CONFIG__ и разделитель __ для вложенности:
        - APP_CONFIG__DB__URL: URL базы данных
        - APP_CONFIG__RUN__HOST: хост для запуска
        - APP_CONFIG__RUN__PORT: порт для запуска
        - APP_CONFIG__LOGGING__LEVEL: уровень логирования
        - APP_CONFIG__LOGGING__DIRECTORY: папка для логов
        - APP_CONFIG__LOGGING__MAX_SIZE: максимальный размер файла лога
        - APP_CONFIG__LOGGING__BACKUP_COUNT: количество файлов бэкапа
        - APP_CONFIG__SUPERADMIN__LOGIN: логин суперадминистратора
        - APP_CONFIG__SUPERADMIN__PASSWORD: пароль суперадминистратора

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
        extra="ignore",  # Игнорируем лишние поля из .env файла
    )

    run: RunConfig = RunConfig()
    db: DatabaseConfig
    logging: LoggingConfig = LoggingConfig()
    superadmin: SuperAdminConfig


settings = Settings()
