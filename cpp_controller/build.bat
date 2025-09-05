@echo off
REM Скрипт сборки TOTP Controller для Windows

echo === Сборка TOTP Controller ===

REM Проверка наличия CMake
cmake --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: CMake не найден. Установите CMake.
    exit /b 1
)

echo CMake найден.

REM Создание директории сборки
if exist build (
    echo Очистка предыдущей сборки...
    rmdir /s /q build
)

mkdir build
cd build

echo Конфигурация проекта...
cmake ..

if errorlevel 1 (
    echo Ошибка конфигурации проекта.
    exit /b 1
)

echo Сборка проекта...
cmake --build . --config Release

if errorlevel 1 (
    echo Ошибка сборки проекта.
    exit /b 1
)

echo === Сборка завершена ===
echo Исполняемый файл: build\Release\totp_controller.exe
echo.
echo Для запуска:
echo   cd build\Release && totp_controller.exe
echo.
echo Или:
echo   build\Release\totp_controller.exe
