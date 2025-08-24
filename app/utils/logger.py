import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import settings


def setup_logging() -> None:
    """Настраивает систему логирования на основе конфигурации.

    Функция настраивает loguru для работы с:
    - Выводом в консоль (если включено)
    - Записью в файлы с ротацией (если включено)
    - Настраиваемым форматом и уровнем логирования
    - Автоматическим созданием папки для логов

    Настройки берутся из settings.logging:
    - level: уровень логирования
    - format: формат сообщений
    - directory: папка для хранения логов
    - max_size: максимальный размер файла лога
    - backup_count: количество файлов бэкапа
    - console_output: включение/выключение вывода в консоль
    - file_output: включение/выключение записи в файлы
    """
    # Убираем стандартный обработчик loguru
    logger.remove()

    # Создаем папку для логов, если она не существует
    log_dir = Path(settings.logging.directory)
    log_dir.mkdir(exist_ok=True)

    # Настраиваем формат логов
    log_format = settings.logging.format

    # Добавляем вывод в консоль, если включено
    if settings.logging.console_output:
        logger.add(
            sys.stdout,
            format=log_format,
            level=settings.logging.level,
            colorize=True,
        )

    # Добавляем запись в файлы, если включено
    if settings.logging.file_output:
        # Основной файл логов
        main_log_file = log_dir / "app.log"
        logger.add(
            main_log_file,
            format=log_format,
            level=settings.logging.level,
            rotation=f"{settings.logging.max_size} MB",
            retention=settings.logging.backup_count,
            compression="zip",
            encoding="utf-8",
        )

        # Файл для ошибок
        error_log_file = log_dir / "error.log"
        logger.add(
            error_log_file,
            format=log_format,
            level="ERROR",
            rotation=f"{settings.logging.max_size} MB",
            retention=settings.logging.backup_count,
            compression="zip",
            encoding="utf-8",
        )

        # Файл для отладочной информации
        debug_log_file = log_dir / "debug.log"
        logger.add(
            debug_log_file,
            format=log_format,
            level="DEBUG",
            rotation=f"{settings.logging.max_size} MB",
            retention=settings.logging.backup_count,
            compression="zip",
            encoding="utf-8",
        )

    # Логируем информацию о настройке логирования
    logger.info("Система логирования настроена")
    logger.info(f"Уровень логирования: {settings.logging.level}")
    logger.info(f"Папка для логов: {log_dir.absolute()}")
    console_status = "включен" if settings.logging.console_output else "выключен"
    logger.info(f"Вывод в консоль: {console_status}")
    file_status = "включена" if settings.logging.file_output else "выключена"
    logger.info(f"Запись в файлы: {file_status}")


def get_logger(name: Optional[str] = None) -> "logger":
    """Возвращает настроенный логгер.

    Args:
        name: Имя логгера (обычно __name__ модуля).

    Returns:
        logger: Настроенный экземпляр loguru logger.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Сообщение для логирования")
    """
    if name:
        return logger.bind(name=name)
    return logger


# Автоматически настраиваем логирование при импорте модуля
setup_logging()
