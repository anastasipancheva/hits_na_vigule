from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import logging
import os

from controller.database import get_db

# Создаем директорию для шаблонов если не существует
os.makedirs("templates/partials", exist_ok=True)

router = APIRouter(prefix="/reader")
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def reader_interface(request: Request):
    """Главный интерфейс считывателя"""
    return templates.TemplateResponse(
        "reader.html",
        {"request": request}
    )


@router.post("/verify-code", response_class=HTMLResponse)
async def verify_code(
        request: Request,
        code: str = Form(...),
        method: str = Form("manual"),
        db: Session = Depends(get_db)
):
    """Обработка кода доступа"""
    try:
        from ...services.reader_service import reader_service
        result = await reader_service.process_access_code(db, code, method)

        return templates.TemplateResponse(
            "partials/result.html",
            {
                "request": request,
                "result": result
            }
        )

    except Exception as e:
        logger.error(f"Ошибка обработки кода: {e}")
        return templates.TemplateResponse(
            "partials/error.html",
            {
                "request": request,
                "error": "Ошибка обработки запроса"
            }
        )


@router.get("/voice-support", response_class=JSONResponse)
async def voice_support():
    """Проверка поддержки голосового ввода"""
    return {
        "supported": True,
        "message": "Используется Web Speech API браузера",
        "requires": "Поддержка браузером SpeechRecognition"
    }


@router.post("/validate-voice", response_class=JSONResponse)
async def validate_voice_text(
        text: str = Form(...),
        db: Session = Depends(get_db)
):
    """Валидация текста из голосового ввода"""
    try:
        from ...services.reader_service import reader_service
        import re

        # Извлекаем цифры из текста
        digits = re.sub(r'\D', '', text)

        if len(digits) != 6:
            return {
                "success": False,
                "message": f"Распознано: '{text}'. Нужно 6 цифр, получено {len(digits)}: {digits}",
                "access_granted": False
            }

        result = await reader_service.process_access_code(db, digits, "voice")
        return result

    except Exception as e:
        logger.error(f"Ошибка валидации голоса: {e}")
        return {
            "success": False,
            "message": "Ошибка обработки голосового ввода",
            "access_granted": False
        }