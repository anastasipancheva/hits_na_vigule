import pyotp
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

from ..database import User
from ..schemas import (
    UserCreateRequest,
    TotpVerifyRequest,
    TotpVerifyResponse,
)


class CryptoService:
    """AEAD AES-GCM шифрование TOTP секретов"""

    def __init__(self, master_key: bytes | None = None):
        # Ключ 256 бит
        if master_key is None:
            # Берем из переменной окружения или генерируем (для dev)
            env_key = os.getenv("MASTER_KEY")
            if env_key:
                self.master_key = bytes.fromhex(env_key)
            else:
                self.master_key = AESGCM.generate_key(bit_length=256)
        else:
            self.master_key = master_key
        self.aesgcm = AESGCM(self.master_key)

    def encrypt(self, plaintext: str, associated_data: bytes | None = None) -> bytes:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), associated_data)
        return nonce + ciphertext  # сохраняем nonce префиксом

    def decrypt(self, blob: bytes, associated_data: bytes | None = None) -> str:
        nonce = blob[:12]
        ciphertext = blob[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, associated_data)
        return plaintext.decode()


crypto_service = CryptoService()


class SecretsService:
    """Сервис пользователей и TOTP с шифрованием секрета"""

    async def create_user(self, db: Session, request: UserCreateRequest) -> User:
        existing = db.query(User).filter(User.username == request.username).first()
        if existing:
            raise ValueError("Пользователь уже существует")
        user = User(
            username=request.username,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    async def save_user_secret(self, db: Session, username: str, secret_plain: str) -> bool:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("Пользователь не найден")
        # Шифруем и сохраняем
        aad = username.encode()
        encrypted = crypto_service.encrypt(secret_plain, associated_data=aad)
        user.totp_secret = encrypted
        db.commit()
        return True

    async def revoke_access(self, db: Session, username: str) -> bool:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("Пользователь не найден")
        user.totp_secret = None
        db.commit()
        return True

    async def delete_user(self, db: Session, username: str) -> bool:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise ValueError("Пользователь не найден")
        db.delete(user)
        db.commit()
        return True

    async def verify_totp(self, db: Session, request: TotpVerifyRequest) -> TotpVerifyResponse:
        user = db.query(User).filter(User.username == request.username).first()
        if not user:
            return TotpVerifyResponse(success=False, message="Пользователь не найден", access_granted=False)
        if user.secret_expires_at and datetime.utcnow() > user.secret_expires_at:
            return TotpVerifyResponse(success=False, message="Срок действия секрета истек", access_granted=False)
        if not user.totp_secret:
            return TotpVerifyResponse(success=False, message="Секрет не установлен", access_granted=False)

        try:
            aad = user.username.encode()
            secret_plain = crypto_service.decrypt(user.totp_secret, associated_data=aad)
        except Exception:
            return TotpVerifyResponse(success=False, message="Ошибка расшифровки секрета", access_granted=False)

        totp = pyotp.TOTP(secret_plain)
        is_valid = totp.verify(request.totp_code, valid_window=1)
        if not is_valid:
            return TotpVerifyResponse(success=False, message="Неверный TOTP код", access_granted=False)
        return TotpVerifyResponse(success=True, message="Доступ разрешен", access_granted=True)


secrets_service = SecretsService()
