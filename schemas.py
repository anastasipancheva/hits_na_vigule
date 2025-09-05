from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserCreateRequest(BaseModel):
    """Создание пользователя"""
    username: str


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
    secret_expires_at: Optional[datetime]
    created_at: datetime
    has_secret: bool

    class Config:
        from_attributes = True
