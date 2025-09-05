import os

from fastapi import FastAPI, HTTPException
from starlette.templating import Jinja2Templates

from .api.endpoints import controller, reader
from .services.rsa_service import rsa_service
from fastapi.staticfiles import StaticFiles
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Door Controller API",
    description="API для контроллера двери с TOTP аутентификацией",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация RSA ключей при старте приложения
@app.on_event("startup")
async def startup_event():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Инициализация RSA ключей (попытка {attempt + 1}/{max_retries})...")
            rsa_service.load_keys()

            # Проверяем что ключи работают
            if rsa_service.ensure_keys_loaded():
                public_key = rsa_service.get_public_key_pem()
                logger.info(f"✅ RSA ключи инициализированы. Публичный ключ готов.")
                return
            else:
                logger.warning("Проверка ключей не прошла, пробуем снова...")
                time.sleep(1)

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RSA ключей (попытка {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.critical("❌ Не удалось инициализировать RSA ключи после всех попыток")
                # В зависимости от требований, можно либо завершить работу,
                # либо продолжить в degraded mode
                raise RuntimeError("Не удалось инициализировать RSA ключи")
            time.sleep(2)


app.include_router(controller.router)
app.include_router(reader.router)


@app.get("/")
async def root():
    return {"message": "Door Controller API работает!"}


# @app.get("/health")
# async def health_check():
#     try:
#         # Проверяем что RSA сервис работает
#         rsa_service.get_public_key_pem()
#         return {"status": "healthy", "rsa_keys": "ok", "service": "door_controller"}
#     except Exception as e:
#         return {"status": "degraded", "rsa_keys": "error", "error": str(e), "service": "door_controller"}
#
#
# @app.get("/debug/rsa-keys")
# async def debug_rsa_keys():
#     """Эндпоинт для отладки RSA ключей"""
#     try:
#         public_key = rsa_service.get_public_key_pem()
#         key_info = {
#             "public_key_length": len(public_key),
#             "public_key_first_50": public_key[:50] + "..." if len(public_key) > 50 else public_key,
#             "private_key_loaded": rsa_service._private_key is not None,
#             "public_key_loaded": rsa_service._public_key is not None,
#             "keys_directory": rsa_service.keys_dir,
#             "private_key_exists": os.path.exists(rsa_service.private_key_path),
#             "public_key_exists": os.path.exists(rsa_service.public_key_path)
#         }
#         return key_info
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"RSA keys error: {str(e)}")