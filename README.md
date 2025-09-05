# Door Controller
Контроллер реализован в двух вариантах:
- FastAPI python бэкенд + Web с поддержкой сетевого взаимодействия с панелью администратора для удобства администрирования
- Полностью автономное C++ CLI приложение под Linux, оптимизированное под легковесные устройства

# 1. FastAPI бэкенд

Путь:
```
/controller
```

## Функциональность

- Добавление новых пользователей
- Занесения TOTP секрета в БД
- Верификация TOTP кодов
- Управление пользователями и их секретами

## Установка

```bash
docker-compose up --build
```

## Документация
```
http://locaLhost:8000/docs
```

## Интерфейс
```
http://locaLhost:8000/reader
```

# 2. C++ CLI приложение

Путь:
```
/cpp_controller
```

## Установка (Linux)

Установка зависимостей
```bash
sudo apt-get update
sudo apt-get install build-essential cmake libsqlite3-dev libssl-dev pkg-config
```

Сборка и запуск
```bash
cd cpp_controller
./build_linux.sh
./build/totp_controller
```

## Пример работы (Powershell):

```shell
> create_user testuser
Пользователь 'testuser' успешно создан

> save_secret testuser JBSWY3DPEHPK3PXP
Секрет для пользователя 'testuser' успешно сохранен

> verify testuser 123456
✓ Доступ разрешен

> show_user testuser
Информация о пользователе:
  ID: 550e8400-e29b-41d4-a716-446655440000
  Имя: testuser
  Секрет установлен: Да
  Создан: 2025-01-15T10:30:00Z

> quit
До свидания!
```

# База данных

Используется SQLite база данных `controller.db` с таблицей `users`:
- `id` - уникальный идентификатор
- `username` - уникальное имя пользователя
- `totp_secret` - секрет для TOTP (может быть NULL)
- `access_expires_at` - дата окончания действия доступа
- `created_at` - дата создания пользователя
