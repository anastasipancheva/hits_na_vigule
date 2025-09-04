#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации работы Door Controller API
"""

import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000/controller"

def test_api():
    """Тестирование основных функций API"""
    
    print("🚪 Тестирование Door Controller API")
    print("=" * 50)
    
    # 1. Создание пользователя
    print("\n1. Создание пользователя...")
    user_data = {
        "username": "test_user",
        "access_expires_at": (datetime.now() + timedelta(days=30)).isoformat()
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Пользователь создан: {user['username']}")
            print(f"   ID: {user['id']}")
            print(f"   Доступ до: {user['access_expires_at']}")
        else:
            print(f"❌ Ошибка создания пользователя: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу. Убедитесь, что сервер запущен.")
        return
    
    # 2. Получение секрета
    print("\n2. Получение TOTP секрета...")
    try:
        response = requests.get(f"{BASE_URL}/users/test_user/secret")
        if response.status_code == 200:
            secret_data = response.json()
            print(f"✅ Секрет получен для пользователя: {secret_data['username']}")
            print(f"   TOTP секрет: {secret_data['totp_secret']}")
            print(f"   QR код сгенерирован: {'Да' if secret_data['qr_code_url'] else 'Нет'}")
            
            # Сохраняем секрет для тестирования
            totp_secret = secret_data['totp_secret']
        else:
            print(f"❌ Ошибка получения секрета: {response.text}")
            return
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # 3. Генерация тестового TOTP кода
    print("\n3. Генерация тестового TOTP кода...")
    try:
        import pyotp
        totp = pyotp.TOTP(totp_secret)
        current_code = totp.now()
        print(f"✅ Текущий TOTP код: {current_code}")
    except ImportError:
        print("❌ Модуль pyotp не установлен. Установите: pip install pyotp")
        return
    except Exception as e:
        print(f"❌ Ошибка генерации TOTP: {e}")
        return
    
    # 4. Верификация TOTP
    print("\n4. Верификация TOTP кода...")
    verify_data = {
        "username": "test_user",
        "totp_code": current_code
    }
    
    try:
        response = requests.post(f"{BASE_URL}/verify", json=verify_data)
        if response.status_code == 200:
            verify_result = response.json()
            print(f"✅ Результат верификации:")
            print(f"   Успех: {verify_result['success']}")
            print(f"   Сообщение: {verify_result['message']}")
            print(f"   Доступ разрешен: {verify_result['access_granted']}")
        else:
            print(f"❌ Ошибка верификации: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 5. Список пользователей
    print("\n5. Получение списка пользователей...")
    try:
        response = requests.get(f"{BASE_URL}/users")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Найдено пользователей: {len(users)}")
            for user in users:
                print(f"   - {user['username']} (ID: {user['id']}, Секрет: {'Есть' if user['has_secret'] else 'Нет'})")
        else:
            print(f"❌ Ошибка получения списка: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_api()
