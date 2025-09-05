from __future__ import annotations

import pyotp
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import true, false
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import logging
import time

# Настройка логгера
logger = logging.getLogger(__name__)

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

from .rsa_service import rsa_service
from ..schemas import EncryptedSecretRequest

from ..database import User
from ..schemas import (
    UserCreateRequest,
    TotpVerifyRequest,
    TotpVerifyResponse,
    UserType,
)


class CryptoService:
    """AEAD AES-GCM шифрование TOTP секретов с надежным хранением Master Key"""

    def __init__(self, master_key_path: str = "./secure_keys/master.key"):
        self.master_key_path = master_key_path
        os.makedirs(os.path.dirname(master_key_path), exist_ok=True, mode=0o700)
        self.master_key = self._load_or_generate_master_key()

    def _load_or_generate_master_key(self) -> bytes:
        """Загрузка или генерация Master Key"""
        if os.path.exists(self.master_key_path):
            # Загружаем существующий ключ
            with open(self.master_key_path, 'rb') as f:
                master_key = f.read()
            print("✅ Master Key загружен из файла")
        else:
            # Генерируем новый ключ
            master_key = AESGCM.generate_key(bit_length=256)
            with open(self.master_key_path, 'wb') as f:
                f.write(master_key)
            os.chmod(self.master_key_path, 0o400)  # Только чтение для владельца
            print("✅ Новый Master Key сгенерирован и сохранен")

        return master_key

    def encrypt(self, plaintext: str, associated_data: bytes | None = None) -> bytes:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self.master_key)  # Создаем инстанс для каждого вызова
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), associated_data)
        return nonce + ciphertext

    def decrypt(self, blob: bytes, associated_data: bytes | None = None) -> str:
        nonce = blob[:12]
        ciphertext = blob[12:]
        aesgcm = AESGCM(self.master_key)  # Создаем инстанс для каждого вызова
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)
        return plaintext.decode()


# Глобальный экземпляр с указанием пути
crypto_service = CryptoService(master_key_path="./secure_keys/master.key")


class SecretsService:
    """Сервис пользователей и TOTP с шифрованием секрета"""

    def _calculate_secret_expiry(self, user_type: UserType) -> datetime:
        """Вычисляет срок действия секрета на основе типа пользователя"""
        now = datetime.utcnow()
        
        if user_type == UserType.PERMANENT:
            # Постоянный сотрудник - 1 год
            return now + timedelta(days=365)
        elif user_type == UserType.GUEST:
            # Гость - 7 дней
            return now + timedelta(days=7)
        elif user_type == UserType.BUSINESS_TRIP:
            # Командировка - 30 дней
            return now + timedelta(days=30)
        else:
            # По умолчанию - 30 дней
            return now + timedelta(days=30)

    async def create_user(self, db: Session, request: UserCreateRequest) -> User:
        existing = db.query(User).filter((User.username == request.username) == true()).first()
        if existing:
            raise ValueError("Пользователь уже существует")
        
        # Вычисляем срок действия секрета на основе типа пользователя
        secret_expires_at = self._calculate_secret_expiry(request.user_type)
        
        user = User(
            username=request.username,
            user_type=request.user_type.value,
            secret_expires_at=secret_expires_at,
        )
        
        logger.info(f"👤 Создание пользователя: {request.username}, тип: {request.user_type.value}, срок действия: {secret_expires_at}")
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    async def save_user_secret(self, db: Session, username: str, secret_plain: str) -> bool:
        user = db.query(User).filter((User.username == username) == true()).first()
        if not user:
            raise ValueError("Пользователь не найден")
        # Шифруем и сохраняем
        aad = username.encode()
        encrypted = crypto_service.encrypt(secret_plain, associated_data=aad)
        user.totp_secret = encrypted
        db.commit()
        return True

    async def revoke_access(self, db: Session, username: str) -> bool:
        user = db.query(User).filter((User.username == username) == true()).first()
        if not user:
            raise ValueError("Пользователь не найден")
        user.totp_secret = None
        db.commit()
        return True

    async def delete_user(self, db: Session, username: str) -> bool:
        user = db.query(User).filter((User.username == username) == true()).first()
        if not user:
            raise ValueError("Пользователь не найден")
        db.delete(user)
        db.commit()
        return True

    async def verify_totp(self, db: Session, request: TotpVerifyRequest) -> TotpVerifyResponse:

        # Поиск пользователя
        user = db.query(User).filter((User.username == request.username) == true()).first()
        if not user:
            logger.warning(f"❌ Пользователь не найден: {request.username}")
            return TotpVerifyResponse(success=False, message="Пользователь не найден", access_granted=False)

        logger.info(f"✅ Пользователь найден: {user.username} (ID: {user.id})")

        # Проверка срока действия секрета
        if user.secret_expires_at and datetime.utcnow() > user.secret_expires_at:
            logger.warning(f"⏰ Срок действия секрета истек для {request.username}. Истекает: {user.secret_expires_at}")
            return TotpVerifyResponse(success=False, message="Срок действия секрета истек", access_granted=False)

        if user.secret_expires_at:
            logger.info(f"⏰ Срок действия секрета: {user.secret_expires_at} (активен)")

        # Проверка наличия секрета
        if not user.totp_secret:
            logger.warning(f"🔑 Секрет не установлен для пользователя: {request.username}")
            return TotpVerifyResponse(success=False, message="Секрет не установлен", access_granted=False)

        logger.info(f"🔑 Секрет найден в БД (длина: {len(user.totp_secret)} байт)")

        # Расшифровка секрета
        try:
            aad = user.username.encode()
            secret_plain = crypto_service.decrypt(user.totp_secret, associated_data=aad)
            logger.info(f"🔓 Секрет успешно расшифрован: {secret_plain}")
        except Exception as e:
            logger.error(f"💥 Ошибка расшифровки секрета для {request.username}: {str(e)}")
            return TotpVerifyResponse(success=False, message="Ошибка расшифровки секрета", access_granted=False)

        # Создание HOTP объекта и верификация
        try:
            hotp = pyotp.HOTP(secret_plain)

            # Логируем время сервера в Unix timestamp и читаемом формате
            current_time_seconds = int(time.time())
            current_time_readable = datetime.utcnow()
            logger.info(f"🕐 [СЕРВЕР] Текущее время: {current_time_readable} (Unix: {current_time_seconds})")

            # Вычисляем counter (окно TOTP)
            time_step = 30
            counter = current_time_seconds // time_step
            logger.info(
                f"🕐 [СЕРВЕР] TOTP counter: {counter} (окно: {counter * time_step} - {(counter + 1) * time_step})")

            logger.info(f"🔐 Начало верификации TOTP для пользователя: {request.username}")

            # Генерируем ожидаемый код для текущего counter
            expected_code = hotp.at(counter)
            logger.info(f"🔢 Ожидаемый HOTP код: {expected_code}, Полученный код: {request.totp_code}")

            # Проверяем код
            is_valid = hotp.verify(request.totp_code, counter)

            if is_valid:
                logger.info(f"✅ TOTP код верен для пользователя: {request.username}")
                return TotpVerifyResponse(success=True, message="Доступ разрешен", access_granted=True)
            else:
                logger.warning(f"❌ Неверный TOTP код для пользователя: {request.username}")
                return TotpVerifyResponse(success=False, message="Неверный TOTP код", access_granted=False)

        except Exception as e:
            logger.error(f"💥 Ошибка при создании/верификации TOTP для {request.username}: {str(e)}")
            return TotpVerifyResponse(success=False, message="Ошибка верификации TOTP", access_granted=False)

    async def save_encrypted_secret(self, db: Session, request: EncryptedSecretRequest) -> bool:
        """Сохранение секрета, зашифрованного RSA-ключом контроллера"""
        user = db.query(User).filter((User.username == request.username) == true()).first()
        if not user:
            raise ValueError("Пользователь не найден")

        try:
            # Декодируем из Base64 и расшифровываем RSA
            encrypted_data = base64.b64decode(request.encrypted_secret)
            secret_plain = rsa_service.decrypt_with_private_key(encrypted_data)

            # Шифруем AES-GCM для хранения
            aad = user.username.encode()
            encrypted = crypto_service.encrypt(secret_plain, associated_data=aad)

            user.totp_secret = encrypted
            if request.secret_expires_at:
                user.secret_expires_at = request.secret_expires_at

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise ValueError(f"Ошибка обработки зашифрованного секрета: {str(e)}")


secrets_service = SecretsService()
