# Door Controller API

FastAPI бэкенд для контроллера двери с TOTP аутентификацией.

## Функциональность

- Регистрация новых пользователей с указанием срока действия доступа
- Генерация и выдача TOTP секретов для пользователей
- Верификация TOTP кодов
- Управление пользователями и их секретами

## Установка

Лучше всего через докер:
```bash
docker-compose up --build
```

1. Установите зависимости:
```bash
poetry install
```

2. Запустите сервер:
```bash
python run.py
```

Или используйте uvicorn напрямую:
```bash
uvicorn controller.main:app --reload --host 0.0.0.0 --port 8000
```

## API Эндпоинты

### 1. Создание пользователя
```
POST /controller/users
```
Тело запроса:
```json
{
    "username": "user1",
    "access_expires_at": "2024-12-31T23:59:59"
}
```

### 2. Получение секрета для пользователя
```
GET /controller/users/{username}/secret
```

### 3. Верификация TOTP
```
POST /controller/verify
```
Тело запроса:
```json
{
    "username": "user1",
    "totp_code": "123456"
}
```

### 4. Сброс секрета пользователя
```
DELETE /controller/users/{username}/secret
```

### 5. Список всех пользователей
```
GET /controller/users
```

## База данных

Используется SQLite база данных `controller.db` с таблицей `users`:
- `id` - уникальный идентификатор
- `username` - уникальное имя пользователя
- `totp_secret` - секрет для TOTP (может быть NULL)
- `access_expires_at` - дата окончания действия доступа
- `created_at` - дата создания пользователя

## Документация API

После запуска сервера документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
