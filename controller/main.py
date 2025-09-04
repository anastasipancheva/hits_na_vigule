from fastapi import FastAPI
from .api.endpoints import controller

app = FastAPI(
    title="Door Controller API",
    description="API для контроллера двери с TOTP аутентификацией",
    version="1.0.0"
)

app.include_router(controller.router)


@app.get("/")
async def root():
    return {"message": "Door Controller API работает!"}