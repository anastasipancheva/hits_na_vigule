#!/bin/bash

# Скрипт сборки TOTP Controller для Linux

set -e

echo "=== Сборка TOTP Controller ==="

# Проверка зависимостей
echo "Проверка зависимостей..."

if ! command -v cmake &> /dev/null; then
    echo "Ошибка: CMake не найден. Установите CMake."
    echo "sudo apt install cmake"
    exit 1
fi

if ! command -v g++ &> /dev/null; then
    echo "Ошибка: g++ не найден. Установите build-essential."
    echo "sudo apt install build-essential"
    exit 1
fi

# Проверка библиотек
if ! ldconfig -p | grep -q libsqlite3; then
    echo "Предупреждение: libsqlite3 не найдена. Установите:"
    echo "sudo apt install libsqlite3-dev"
fi

if ! ldconfig -p | grep -q libssl; then
    echo "Предупреждение: libssl не найдена. Установите:"
    echo "sudo apt install libssl-dev"
fi

echo "Основные зависимости найдены."

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
echo "  ./build/totp_controller"
echo ""
echo "Если есть ошибки с зависимостями, установите:"
echo "  sudo apt install libsqlite3-dev libssl-dev"
