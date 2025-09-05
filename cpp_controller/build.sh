#!/bin/bash

# Скрипт сборки TOTP Controller

set -e

echo "=== Сборка TOTP Controller ==="

# Проверка зависимостей
echo "Проверка зависимостей..."

if ! command -v cmake &> /dev/null; then
    echo "Ошибка: CMake не найден. Установите CMake."
    exit 1
fi

if ! pkg-config --exists sqlite3; then
    echo "Ошибка: SQLite3 не найден. Установите libsqlite3-dev."
    exit 1
fi

if ! pkg-config --exists openssl; then
    echo "Ошибка: OpenSSL не найден. Установите libssl-dev."
    exit 1
fi

echo "Все зависимости найдены."

# Создание директории сборки
if [ -d "build" ]; then
    echo "Очистка предыдущей сборки..."
    rm -rf build
fi

mkdir build
cd build

echo "Конфигурация проекта..."
cmake ..

echo "Сборка проекта..."
make -j$(nproc)

echo "=== Сборка завершена ==="
echo "Исполняемый файл: build/totp_controller"
echo ""
echo "Для запуска:"
echo "  cd build && ./totp_controller"
echo ""
echo "Или:"
echo "  ./build/totp_controller"
