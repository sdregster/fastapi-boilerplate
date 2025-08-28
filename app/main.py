from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
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
        docs_url=None,
        redoc_url=None,
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

    # Обработчики исключений
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Обрабатывает HTTP исключения FastAPI и логирует их.

        - 4xx логируются как WARNING
        - 5xx логируются как ERROR (попадает в error.log)
        """
        if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            msg = (
                f"HTTP {exc.status_code} ошибка для {request.method} {request.url}: "
                f"{exc.detail}"
            )
            logger.exception(msg)
        else:
            msg = (
                f"HTTP {exc.status_code} для {request.method} {request.url}: "
                f"{exc.detail}"
            )
            logger.warning(msg)
        return ORJSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Глобальный обработчик неперехваченных исключений.

        Логирует ошибку с трейсбеком и возвращает 500.
        """
        msg = f"Неперехваченное исключение при {request.method} {request.url}: {exc}"
        logger.exception(msg)
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal Server Error"},
        )

    # Монтирование статических файлов
    app.mount("/static", StaticFiles(directory="static"), name="static")
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

    @root_router.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )

    @root_router.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect():
        return get_swagger_ui_oauth2_redirect_html()

    @root_router.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )

    # Подключение роутеров
    app.include_router(root_router, tags=["root"])
    app.include_router(router_auth, prefix="/auth", tags=["Auth"])
    logger.info("🔗 Роутеры подключены: root, auth")


# Создание экземпляра приложения
app = create_app()
logger.info("🎉 FastAPI приложение успешно создано и готово к работе!")
