from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum


class UserType(str, Enum):
    """Типы пользователей"""
    PERMANENT = "permanent"  # Постоянный сотрудник - 1 год
    GUEST = "guest"         # Гость - 7 дней
    BUSINESS_TRIP = "business_trip"  # Командировка - 30 дней


class UserCreateRequest(BaseModel):
    """Создание пользователя"""
    username: str
    user_type: UserType


class SaveSecretRequest(BaseModel):
    """Сохранение секрета (устанавливает/обновляет)"""
    username: str
    secret_plain: str  # base32 секрет TOTP
    secret_expires_at: Optional[datetime] = None


class TotpVerifyRequest(BaseModel):
    username: str
    totp_code: str


class TotpVerifyResponse(BaseModel):
    success: bool
    message: str
    access_granted: bool


class UserResponse(BaseModel):
    id: str
    username: str
    user_type: UserType
    secret_expires_at: Optional[datetime]
    created_at: datetime
    has_secret: bool

    class Config:
        from_attributes = True


class EncryptedSecretRequest(BaseModel):
    """Запрос для сохранения зашифрованного секрета"""
    username: str
    encrypted_secret: str = Field(..., description="Base64-encoded RSA-encrypted TOTP secret")
    secret_expires_at: Optional[datetime] = None


class PublicKeyResponse(BaseModel):
    """Ответ с публичным ключом контроллера"""
    public_key: str
