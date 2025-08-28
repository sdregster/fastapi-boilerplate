# 🚀 Инициализация FastAPI проекта

## 📋 Последовательность действий

### 1. Настройка переменных окружения
Создайте файл `.env` с обязательными переменными:

```env
# База данных
APP_CONFIG__DB__URL=postgresql+asyncpg://username:password@localhost:5432/dbname

# Суперадминистратор
APP_CONFIG__SUPERADMIN__LOGIN=admin
APP_CONFIG__SUPERADMIN__PASSWORD=secure_password_123
```

### 2. Запуск скрипта инициализации
```bash
python init_project.py
```

## 🔐 Что создается
- Таблицы `roles` и `users`
- Роли: User, Guest, Admin, SuperAdmin
- Первый пользователь с ролью SuperAdmin

## 🚀 Запуск приложения
```bash
uvicorn app.main:app --reload
```
