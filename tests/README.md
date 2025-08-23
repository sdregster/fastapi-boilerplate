# Тестирование FastAPI бойлерплейта

## Обзор

Этот проект использует pytest для тестирования. Тесты организованы в четкую структуру по типам и покрывают все основные компоненты системы.

### Типы тестов

- **Модульные тесты** (`tests/unit/`) - тестируют отдельные компоненты изолированно
- **Интеграционные тесты** (`tests/integration/`) - тестируют взаимодействие компонентов
- **End-to-End тесты** (`tests/e2e/`) - тестируют полные сценарии работы приложения

## Структура тестов

```
tests/
├── __init__.py              # Инициализация пакета тестов
├── conftest.py              # Конфигурация pytest и общие фикстуры
├── unit/                    # Модульные тесты
│   ├── __init__.py
│   ├── test_id_mixin.py    # Тесты для IdMixin
│   ├── test_timestamp_mixin.py # Тесты для TimestampMixin
│   └── test_base_mixin.py  # Тесты для BaseMixin
├── integration/             # Интеграционные тесты
│   ├── __init__.py
│   └── test_mixins_integration.py # Тесты взаимодействия миксинов
├── e2e/                    # End-to-end тесты
│   ├── __init__.py
│   └── test_full_workflow.py # Полные сценарии работы
└── README.md               # Этот файл
```

## Запуск тестов

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск всех тестов
```bash
pytest
```

### Запуск с подробным выводом
```bash
pytest -v
```

### Запуск конкретного файла тестов
```bash
pytest tests/unit/test_id_mixin.py
```

### Запуск конкретного теста
```bash
pytest tests/unit/test_id_mixin.py::TestIdMixin::test_id_field_attributes
```

### Запуск с покрытием кода
```bash
pytest --cov=app
```

## Фикстуры

### engine
Создает тестовый движок SQLite в памяти для изоляции тестов.

### db_session
Создает тестовую сессию базы данных с автоматическим созданием таблиц.

### test_model_class
Возвращает класс тестовой модели со всеми миксинами для тестирования.

## Маркеры тестов

- `@pytest.mark.e2e` - end-to-end тесты (медленные, полные сценарии)
- `@pytest.mark.integration` - интеграционные тесты (взаимодействие компонентов)
- `@pytest.mark.unit` - модульные тесты (отдельные компоненты)

## Написание новых тестов

### Структура теста
```python
def test_function_name(self) -> None:
    """Краткое описание что тестируется."""
    # Arrange - подготовка данных
    # Act - выполнение действия
    # Assert - проверка результата
```

### Импорты для типизации
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture
```

### Использование фикстур
```python
def test_with_fixture(self, test_model_class) -> None:
    """Тест с использованием фикстуры."""
    model_class = test_model_class
    # ... тест
```

## Лучшие практики

1. **Изоляция тестов** - каждый тест должен быть независимым
2. **Описательные имена** - имена тестов должны объяснять что тестируется
3. **Типизация** - все функции должны иметь аннотации типов
4. **Документация** - каждый тест должен иметь docstring
5. **Фикстуры** - используйте фикстуры для общей логики
6. **Маркеры** - помечайте тесты соответствующими маркерами

## Отладка тестов

### Запуск с отладкой
```bash
pytest --pdb
```

### Запуск с остановкой на первой ошибке
```bash
pytest -x
```

### Запуск с максимальным выводом
```bash
pytest -s -v
```
