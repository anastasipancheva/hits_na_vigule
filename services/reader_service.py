import logging
from datetime import datetime

from sqlalchemy.orm import Session
from ..schemas import TotpVerifyRequest
from .secrets_service import secrets_service
from ..database import User
import re  # Используем regex вместо filter

logger = logging.getLogger(__name__)


class ReaderService:
    """Сервис для работы считывателя"""

    async def process_access_code(self, db: Session, code: str, method: str) -> dict:
        """
        Обработка кода доступа от считывателя
        """
        logger.info(f"Получен код доступа методом {method}: {code}")

        # Очистка кода с помощью regex (замена filter)
        clean_code = re.sub(r'\D', '', code)  # Удаляем все не-цифры

        if len(clean_code) != 6:
            return {
                "success": False,
                "message": "Неверный формат кода. Должно быть 6 цифр.",
                "access_granted": False,
                "code": code,
                "method": method
            }

        # Ищем пользователя по коду
        users = db.query(User).all()

        for user in users:
            if not user.totp_secret:
                continue

            # Проверяем срок действия
            if user.secret_expires_at and datetime.utcnow() > user.secret_expires_at:
                continue

            try:
                request = TotpVerifyRequest(
                    username=user.username,
                    totp_code=clean_code
                )

                response = await secrets_service.verify_totp(db, request)

                if response.access_granted:
                    logger.info(f"Доступ разрешен для пользователя: {user.username}")
                    return {
                        "success": True,
                        "message": f"Доступ разрешен! Добро пожаловать, {user.username}",
                        "access_granted": True,
                        "username": user.username,
                        "code": clean_code,
                        "method": method
                    }

            except Exception as e:
                logger.error(f"Ошибка проверки кода для {user.username}: {e}")
                continue

        return {
            "success": False,
            "message": "Неверный код доступа",
            "access_granted": False,
            "code": clean_code,
            "method": method
        }


reader_service = ReaderService()