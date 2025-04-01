# Сервис сокращения URL

Высокопроизводительный сервис сокращения URL на основе FastAPI с аутентификацией пользователей, аналитикой и кэшированием Redis.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## Возможности

- **Базовая функциональность**:
  - Сокращение URL с автоматической генерацией кода или пользовательским алиасом
  - Перенаправление по коротким ссылкам
  - Обновление и удаление созданных ссылок
  - Поиск ссылок по оригинальному URL
  - Управление сроком жизни ссылок

- **Расширенная функциональность**:
  - Регистрация и аутентификация пользователей с JWT-токенами
  - Подробная статистика посещений по каждой ссылке
  - Организация ссылок по проектам
  - Возможность создания ссылок для неавторизованных пользователей
  - Автоматическая очистка просроченных и неактивных ссылок

- **Производительность**:
  - Высокоскоростное кэширование в Redis для часто используемых ссылок
  - Оптимизированные запросы к базе данных
  - Асинхронные фоновые задачи

## Архитектура компонентов

### База данных

Проект использует PostgreSQL для хранения всех данных. Основные таблицы:

1. **users** - информация о пользователях системы
   - `id`: первичный ключ
   - `email`: email пользователя (уникальный)
   - `username`: опциональное имя пользователя
   - `hashed_password`: хэшированный пароль
   - `is_active`: статус активации аккаунта
   - `created_at`: дата создания аккаунта

2. **links** - сокращенные ссылки
   - `id`: первичный ключ
   - `original_url`: оригинальный URL
   - `short_code`: сгенерированный короткий код
   - `custom_alias`: пользовательский алиас (опционально)
   - `created_at`: дата создания
   - `expires_at`: дата истечения срока (опционально)
   - `last_accessed`: дата последнего обращения
   - `access_count`: счетчик обращений
   - `is_active`: статус ссылки
   - `project`: название проекта (опционально)
   - `owner_id`: внешний ключ к таблице пользователей

3. **link_stats** - статистика переходов по ссылкам
   - `id`: первичный ключ
   - `link_id`: внешний ключ к таблице ссылок
   - `accessed_at`: время доступа
   - `ip_address`: IP-адрес пользователя
   - `user_agent`: User-Agent браузера
   - `referer`: Источник перехода
   - `country`: Страна посетителя (опционально)

### Кэширование

Система использует Redis для кэширования данных, что значительно увеличивает производительность:

1. **Кэширование ссылок**: Часто используемые ссылки кэшируются в Redis для быстрого перенаправления без обращения к базе данных.
   - Ключ: `link:{short_code}`
   - Значение: оригинальный URL
   - TTL: 24 часа (86400 секунд)

2. **Кэширование статистики**: Статистика популярных ссылок кэшируется для быстрого доступа.
   - Ключ: `stats:{short_code}`
   - Значение: JSON с данными статистики
   - TTL: 5 минут (300 секунд)

3. **Инвалидация кэша**: При изменении или удалении ссылки кэш автоматически сбрасывается.

### Фоновые задачи

Система запускает асинхронные фоновые задачи для обслуживания:

1. **Очистка истекших ссылок**: Автоматическое удаление ссылок, у которых истек срок действия.
2. **Очистка неактивных ссылок**: Удаление ссылок, которые не использовались в течение определенного периода (по умолчанию 30 дней).

- **Базовая функциональность**:
  - Сокращение URL с автоматической генерацией кода или пользовательским алиасом
  - Перенаправление по коротким ссылкам
  - Обновление и удаление созданных ссылок
  - Поиск ссылок по оригинальному URL
  - Управление сроком жизни ссылок

- **Расширенная функциональность**:
  - Регистрация и аутентификация пользователей с JWT-токенами
  - Подробная статистика посещений по каждой ссылке
  - Организация ссылок по проектам
  - Возможность создания ссылок для неавторизованных пользователей
  - Автоматическая очистка просроченных и неактивных ссылок

- **Производительность**:
  - Высокоскоростное кэширование в Redis для часто используемых ссылок
  - Оптимизированные запросы к базе данных
  - Асинхронные фоновые задачи

## Технический стек

- **Backend**: FastAPI, Python 3.9+
- **База данных**: PostgreSQL
- **Кэширование**: Redis
- **Аутентификация**: JWT (JSON Web Tokens)
- **Миграции**: Alembic
- **Контейнеризация**: Docker, Docker Compose
- **Тестирование**: Pytest

## Установка и запуск

### Использование Docker (рекомендуется)

1. Клонируйте репозиторий:
```bash
git clone https://github.com/NesterovEvgeniy/url-shortener.git
cd url-shortener
```

2. Настройте переменные окружения в файле `.env` или используйте значения по умолчанию в `docker-compose.yml`:
```
DATABASE_URL=postgresql://user:password@postgres:5432/urlshortener
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
```

3. Запустите приложение с помощью Docker Compose:
```bash
docker-compose up -d
```

4. Приложение будет доступно по адресу: `http://localhost:8000`
   - Документация API (Swagger): `http://localhost:8000/docs`

### Ручная установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/NesterovEvgeniy/url-shortener.git
cd url-shortener
```

2. Создайте и активируйте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/urlshortener"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="your-secret-key"
```

5. Выполните миграции базы данных:
```bash
alembic upgrade head
```

6. Запустите сервер:
```bash
uvicorn app.main:app --reload
```

## Структура проекта

```
├── .pytest_cache/            # Кэш тестов
├── alembic/                  
│   ├── env.py                # Конфигурация миграций
│   ├── script.py.mako        # Шаблон для генерации миграций
│   └── versions/             # История миграций
├── app/
│   ├── routers/              # Роутеры API
│   │   ├── auth.py           # Аутентификация
│   │   └── links.py          # Управление ссылками
│   ├── database.py           # Подключение к БД
│   ├── main.py               # Точка входа приложения
│   ├── models.py             # Модели SQLAlchemy
│   ├── redis_client.py       # Клиент Redis
│   ├── schemas.py            # Pydantic схемы
│   └── tasks.py              # Фоновые задачи
├── tests/                    # Тесты
│   ├── conftest.py           # Фикстуры pytest
│   ├── test_auth.py          # Тесты аутентификации
│   ├── test_links.py         # Тесты ссылок
│   └── test_cache.py         # Тесты кэширования
├── create_tables.py          # Скрипт инициализации БД
├── docker-compose.yml        # Docker Compose конфиг
├── Dockerfile                # Сборка Docker образа
├── entrypoint.sh             # Скрипт запуска
├── requirements.txt          # Зависимости Python
├── alembic.ini               # Конфигурация Alembic
└── README.md                 # Документация проекта
```

## API документация

### Аутентификация

#### Регистрация нового пользователя

```http
POST /auth/register
```

Запрос:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

Ответ:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```


#### Получение токена доступа (авторизация)

```http
POST /auth/token
```

Запрос (form-data):
```
username: user@example.com
password: secure_password
```

Ответ:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Управление ссылками

#### Создание короткой ссылки

```http
POST /links/shorten
```

Запрос:
```json
{
  "original_url": "https://example.com/very-long-url-path",
  "custom_alias": "my-custom", // опционально
  "expires_at": "2024-03-01T12:00:00Z", // опционально
  "project": "my-project" // опционально
}
```

Ответ:
```json
{
  "id": 1,
  "original_url": "https://example.com/very-long-url-path",
  "short_code": "my-custom",
  "custom_alias": "my-custom",
  "created_at": "2023-03-01T10:00:00Z",
  "expires_at": "2024-03-01T12:00:00Z",
  "last_accessed": null,
  "access_count": 0,
  "owner_id": 1,
  "project": "my-project"
}
```

#### Получение информации о ссылке

```http
GET /links/{short_code}
```

Ответ:
```json
{
  "id": 1,
  "original_url": "https://example.com/very-long-url-path",
  "short_code": "abc123",
  "custom_alias": "my-custom",
  "created_at": "2023-03-01T10:00:00Z",
  "expires_at": "2024-03-01T12:00:00Z",
  "last_accessed": "2023-03-01T11:00:00Z",
  "access_count": 5,
  "owner_id": 1,
  "project": "my-project"
}
```

#### Обновление ссылки

```http
PUT /links/{short_code}
```

Запрос:
```json
{
  "original_url": "https://new-example.com/updated-path",
  "custom_alias": "new-alias", // опционально
  "expires_at": "2025-03-01T12:00:00Z" // опционально
}
```

Ответ:
```json
{
  "id": 1,
  "original_url": "https://new-example.com/updated-path",
  "short_code": "abc123",
  "custom_alias": "new-alias",
  "created_at": "2023-03-01T10:00:00Z",
  "expires_at": "2025-03-01T12:00:00Z",
  "last_accessed": "2023-03-01T11:00:00Z",
  "access_count": 5,
  "owner_id": 1,
  "project": "my-project"
}
```

#### Удаление ссылки

```http
DELETE /links/{short_code}
```

Ответ:
```json
{
  "message": "Link deleted successfully"
}
```

#### Перенаправление по короткой ссылке

```http
GET /{short_code}
```

Ответ: HTTP 302 перенаправление на оригинальный URL

### Статистика и аналитика

#### Получение статистики ссылки

```http
GET /links/{short_code}/stats
```

Ответ:
```json
{
  "original_url": "https://example.com/very-long-url-path",
  "created_at": "2023-03-01T10:00:00Z",
  "access_count": 42,
  "last_accessed": "2023-03-15T14:30:00Z"
}
```

### Поиск ссылок

#### Поиск по оригинальному URL

```http
GET /links/search?original_url=example.com
```

Ответ:
```json
[
  {
    "id": 1,
    "original_url": "https://example.com/very-long-url-path",
    "short_code": "abc123",
    "custom_alias": "my-custom",
    "created_at": "2023-03-01T10:00:00Z",
    "expires_at": "2024-03-01T12:00:00Z",
    "last_accessed": "2023-03-01T11:00:00Z",
    "access_count": 5,
    "owner_id": 1,
    "project": "my-project"
  },
  {
    "id": 2,
    "original_url": "https://example.com/another-path",
    "short_code": "def456",
    "custom_alias": null,
    "created_at": "2023-03-02T10:00:00Z",
    "expires_at": null,
    "last_accessed": "2023-03-02T11:00:00Z",
    "access_count": 3,
    "owner_id": 1,
    "project": "my-project"
  }
]
```

### Управление проектами

#### Получение списка проектов пользователя

```http
GET /links/projects
```

Ответ:
```json
[
  "my-project",
  "work-links",
  "personal"
]
```

#### Получение ссылок проекта

```http
GET /links/projects/{project_name}
```

Ответ:
```json
[
  {
    "id": 1,
    "original_url": "https://example.com/very-long-url-path",
    "short_code": "abc123",
    "custom_alias": "my-custom",
    "created_at": "2023-03-01T10:00:00Z",
    "expires_at": "2024-03-01T12:00:00Z",
    "last_accessed": "2023-03-01T11:00:00Z",
    "access_count": 5,
    "owner_id": 1,
    "project": "my-project"
  }
]
```

## Архитектура компонентов

### База данных

Проект использует PostgreSQL для хранения всех данных. Основные таблицы:

1. **users** - информация о пользователях системы
   - `id`: первичный ключ
   - `email`: email пользователя (уникальный)
   - `username`: опциональное имя пользователя
   - `hashed_password`: хэшированный пароль
   - `is_active`: статус активации аккаунта
   - `created_at`: дата создания аккаунта

2. **links** - сокращенные ссылки
   - `id`: первичный ключ
   - `original_url`: оригинальный URL
   - `short_code`: сгенерированный короткий код
   - `custom_alias`: пользовательский алиас (опционально)
   - `created_at`: дата создания
   - `expires_at`: дата истечения срока (опционально)
   - `last_accessed`: дата последнего обращения
   - `access_count`: счетчик обращений
   - `is_active`: статус ссылки
   - `project`: название проекта (опционально)
   - `owner_id`: внешний ключ к таблице пользователей

3. **link_stats** - статистика переходов по ссылкам
   - `id`: первичный ключ
   - `link_id`: внешний ключ к таблице ссылок
   - `accessed_at`: время доступа
   - `ip_address`: IP-адрес пользователя
   - `user_agent`: User-Agent браузера
   - `referer`: Источник перехода
   - `country`: Страна посетителя (опционально)

### Кэширование

Система использует Redis для кэширования данных, что значительно увеличивает производительность:

1. **Кэширование ссылок**: Часто используемые ссылки кэшируются в Redis для быстрого перенаправления без обращения к базе данных.
   - Ключ: `link:{short_code}`
   - Значение: оригинальный URL
   - TTL: 24 часа (86400 секунд)

2. **Кэширование статистики**: Статистика популярных ссылок кэшируется для быстрого доступа.
   - Ключ: `stats:{short_code}`
   - Значение: JSON с данными статистики
   - TTL: 5 минут (300 секунд)

3. **Инвалидация кэша**: При изменении или удалении ссылки кэш автоматически сбрасывается.

### Фоновые задачи

Система запускает асинхронные фоновые задачи для обслуживания:

1. **Очистка истекших ссылок**: Автоматическое удаление ссылок, у которых истек срок действия.
2. **Очистка неактивных ссылок**: Удаление ссылок, которые не использовались в течение определенного периода (по умолчанию 30 дней).

## Тестирование

Проект имеет комплексное тестовое покрытие более 90% и включает различные типы тестов:

### Структура тестов

- **Юнит-тесты**:
  - `test_auth.py`: Тесты аутентификации (регистрация, вход, JWT-токены)
  - `test_links.py`: Тесты основной логики работы с ссылками
  - `test_cache.py`: Тесты механизма кэширования Redis
  - `test_tasks.py`: Тесты фоновых задач

- **Функциональные тесты**:
  - CRUD-операции для ссылок
  - Механизм перенаправления
  - Обработка невалидных данных
  - Интеграция с базой данных

- **Нагрузочные тесты** (Locust):
  - Сценарии массового создания ссылок
  - Тестирование производительности с Redis-кэшем

### Запуск тестов

1. **Запуск всех тестов**:
```bash
python -m pytest
```

2. **Запуск с отчетом о покрытии**:
```bash
coverage run -m pytest
coverage report  # Текстовый отчет
coverage html    # HTML отчет
```
После выполнения команды `coverage html`, отчет будет доступен в директории `htmlcov/`. Откройте `htmlcov/index.html` в браузере для просмотра детального отчета о покрытии.

![Coverage Report](coverage.png)

3. **Запуск нагрузочного тестирования**:
```bash
locust -f tests/locustfile.py
```
После запуска откройте http://localhost:8089 для доступа к веб-интерфейсу Locust.

![Locust Test](locust.png)
### Требования для запуска тестов

1. Запустите необходимые сервисы с помощью Docker Compose:
```bash
docker-compose up -d
```
Убедитесь, что контейнеры с PostgreSQL и Redis успешно запущены:
```bash
docker-compose ps
```

2. Установите зависимости для тестирования:
```bash
pip install pytest pytest-asyncio pytest-cov coverage locust
```

3. Убедитесь, что сервисы доступны:
   - PostgreSQL (тестовая база данных) на порту 5433
   - Redis (для тестов кэширования) на порту 6379

3. Настройте переменные окружения для тестовой среды:
```bash
export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/test_urlshortener"
export TEST_REDIS_URL="redis://localhost:6379/1"
export TEST_SECRET_KEY="test-secret-key"
```

## Лицензия

Лицензия MIT