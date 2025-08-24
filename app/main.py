from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as router_auth
from app.utils import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    """Управляет жизненным циклом приложения.

    Args:
        app: Экземпляр FastAPI приложения.

    Yields:
        dict: Контекст жизненного цикла.
    """
    logger.info("🚀 Инициализация приложения FastAPI...")
    log_dir = app.state.log_dir if hasattr(app.state, "log_dir") else "logs/"
    logger.info(f"📁 Папка для логов: {log_dir}")
    yield
    logger.info("🛑 Завершение работы приложения FastAPI...")


def create_app() -> FastAPI:
    """Создает и конфигурирует FastAPI приложение.

    Returns:
        FastAPI: Сконфигурированное приложение FastAPI.
    """
    logger.info("🔧 Создание FastAPI приложения...")

    app = FastAPI(
        title="Стартовая сборка FastAPI",
        description=(
            "Современный FastAPI бойлерплейт с SQLAlchemy 2. "
            "Система безопасности, модульная архитектура, "
            "готовые решения для типовых задач.\n\n"
        ),
        version="1.0.0",
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("✅ CORS middleware настроен")

    # Монтирование статических файлов
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    logger.debug("✅ Статические файлы подключены")

    # Регистрация роутеров
    register_routers(app)
    logger.debug("✅ Роутеры зарегистрированы")

    return app


def register_routers(app: FastAPI) -> None:
    """Регистрирует роутеры приложения.

    Args:
        app: Экземпляр FastAPI приложения для регистрации роутеров.
    """
    # Корневой роутер
    root_router = APIRouter()

    @root_router.get("/", tags=["root"])
    def home_page():
        """Возвращает главную страницу приложения.

        Returns:
            dict: Приветственное сообщение.
        """
        logger.debug("📄 Запрос главной страницы")
        return {"message": "Hello World"}

    # Подключение роутеров
    app.include_router(root_router, tags=["root"])
    app.include_router(router_auth, prefix="/auth", tags=["Auth"])
    logger.info("🔗 Роутеры подключены: root, auth")


# Создание экземпляра приложения
app = create_app()
logger.info("🎉 FastAPI приложение успешно создано и готово к работе!")
