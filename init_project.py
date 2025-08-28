#!/usr/bin/env python3
"""
Скрипт инициализации FastAPI проекта.

Выполняет:
1. Проверку переменных окружения
2. Проверку соединения с БД
3. Создание миграции с ролями и первым пользователем
4. Выполнение миграции
"""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Импорты после изменения sys.path
from app.auth.dao import RoleDAO, UsersDAO  # noqa: E402
from app.auth.schemas import (  # noqa: E402
    SDynamicFilter,
    SRoleCreate,
    SUserCreateWithRole,
)
from app.auth.utils import get_password_hash  # noqa: E402
from app.config import settings  # noqa: E402
from app.dao.database import async_session_maker  # noqa: E402


def check_environment_variables() -> bool:
    """Проверяет наличие необходимых переменных окружения.

    Returns:
        bool: True если все переменные найдены, False иначе.
    """
    print("🔍 Проверка переменных окружения...")

    try:
        # Используем настройки из основного приложения
        if not settings.superadmin.login or not settings.superadmin.password:
            print("❌ Отсутствуют переменные окружения для суперадминистратора")
            print("💡 Добавьте в .env:")
            print("   APP_CONFIG__SUPERADMIN__LOGIN=your_superadmin_login")
            print("   APP_CONFIG__SUPERADMIN__PASSWORD=your_superadmin_password")
            return False

        print(f"✅ APP_CONFIG__SUPERADMIN__LOGIN: {settings.superadmin.login}")
        password = settings.superadmin.password
        print(f"✅ APP_CONFIG__SUPERADMIN__PASSWORD: {'*' * len(password)}")
        return True

    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        print("💡 Проверьте правильность .env файла")
        return False


async def check_database_connection() -> bool:
    """Проверяет соединение с базой данных.

    Returns:
        bool: True если соединение успешно, False иначе.
    """
    print("\n🗄️  Проверка соединения с базой данных...")

    try:
        async with async_session_maker() as session:
            # Простая проверка соединения
            await session.execute(text("SELECT 1"))
            print("✅ Соединение с базой данных установлено")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print("💡 Проверьте:")
        print("   - Запущен ли PostgreSQL")
        print("   - Правильность APP_CONFIG__DB__URL в .env")
        print("   - Существование базы данных")
        return False


async def create_initial_data() -> bool:
    """Создает начальные данные: роли и первого пользователя.

    Returns:
        bool: True если данные созданы успешно, False иначе.
    """
    print("\n👥 Создание начальных данных...")

    try:
        print("🔍 Начинаем создание начальных данных...")
        async with async_session_maker() as session:
            print("🔍 Сессия БД создана")
            role_dao = RoleDAO(session)
            user_dao = UsersDAO(session)
            print("🔍 DAO объекты созданы")

            # Проверяем существование ролей
            print("🔍 Проверяем существование ролей...")
            existing_roles = await role_dao.find_all()
            if existing_roles:
                print("⚠️  Роли уже существуют в базе данных")
                return True

            print("🔍 Роли не найдены, создаем новые...")
            # Создаем роли
            roles_data = [
                SRoleCreate(name="Guest"),
                SRoleCreate(name="User"),
                SRoleCreate(name="Admin"),
                SRoleCreate(name="SuperAdmin"),
            ]

            created_roles = []
            for role_data in roles_data:
                print(f"🔍 Создаем роль: {role_data.name}")
                created_role = await role_dao.add(values=role_data)
                created_roles.append(created_role)
                print(f"✅ Создана роль: {created_role.name}")

            # Находим роль SuperAdmin
            print("🔍 Ищем роль SuperAdmin...")
            superadmin_role = next(
                (r for r in created_roles if r.name == "SuperAdmin"), None
            )
            if not superadmin_role:
                print("❌ Роль SuperAdmin не найдена")
                return False

            print(f"🔍 Роль SuperAdmin найдена с ID: {superadmin_role.id}")

            # Проверяем существование пользователя
            print("🔍 Проверяем существование пользователя...")
            existing_user = await user_dao.find_one_or_none(
                filters=SDynamicFilter.create(login=settings.superadmin.login)
            )

            if existing_user:
                print(f"⚠️  Пользователь {settings.superadmin.login} уже существует")
                return True

            print(f"🔍 Создание пользователя с логином: {settings.superadmin.login}")
            print(f"🔍 ID роли SuperAdmin: {superadmin_role.id}")

            # Создаем первого пользователя (суперадминистратора)
            superadmin_data = SUserCreateWithRole(
                login=settings.superadmin.login,
                password=get_password_hash(settings.superadmin.password),
                role_id=superadmin_role.id,
            )

            print(f"🔍 Создан объект схемы: {type(superadmin_data)}")
            print(f"🔍 Данные пользователя: {superadmin_data.model_dump()}")

            await user_dao.add(values=superadmin_data)
            print(f"✅ Создан суперадминистратор: {settings.superadmin.login}")

            # Коммитим все изменения
            await session.commit()
            print("✅ Изменения зафиксированы в базе данных")

            return True

    except Exception as e:
        print(f"❌ Ошибка при создании начальных данных: {e}")
        import traceback

        traceback.print_exc()
        return False


async def run_migrations() -> bool:
    """Запускает миграции базы данных.

    Returns:
        bool: True если миграции выполнены успешно, False иначе.
    """
    print("\n🔄 Выполнение миграций...")

    try:
        import shutil
        import subprocess

        # Проверяем наличие alembic
        if not shutil.which("alembic"):
            print("❌ Alembic не найден. Установите: pip install alembic")
            return False

        # Выполняем миграции
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if result.returncode == 0:
            print("✅ Миграции выполнены успешно")
            return True
        else:
            print("❌ Ошибка при выполнении миграций:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Ошибка при запуске миграций: {e}")
        return False


async def main() -> None:
    """Основная функция инициализации."""
    print("🚀 Инициализация FastAPI проекта")
    print("=" * 50)

    # Проверка переменных окружения
    if not check_environment_variables():
        sys.exit(1)

    # Проверка соединения с БД
    if not await check_database_connection():
        sys.exit(1)

    # Выполнение миграций
    if not await run_migrations():
        sys.exit(1)

    # Создание начальных данных
    if not await create_initial_data():
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🎉 Инициализация проекта завершена успешно!")
    print("\n📋 Что было выполнено:")
    print("   ✅ Проверены переменные окружения")
    print("   ✅ Проверено соединение с БД")
    print("   ✅ Выполнены миграции")
    print("   ✅ Созданы роли пользователей")
    print("   ✅ Создан суперадминистратор")
    print("\n🔐 Данные для входа суперадминистратора:")
    print(f"   Логин: {settings.superadmin.login}")
    print(f"   Пароль: {'*' * len(settings.superadmin.password)}")
    print("\n🚀 Для запуска приложения выполните:")
    print("   uvicorn app.main:app --reload")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Инициализация прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
