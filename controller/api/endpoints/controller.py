from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db, User
from ...services.secrets_service import secrets_service
from ...schemas import (
    UserCreateRequest,
    SaveSecretRequest,
    TotpVerifyRequest,
    TotpVerifyResponse,
    UserResponse,
)

router = APIRouter(prefix="/controller")


@router.post("/users", response_model=UserResponse)
async def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    try:
        user = await secrets_service.create_user(db, request)
        return UserResponse(
            id=user.id,
            username=user.username,
            secret_expires_at=user.secret_expires_at if hasattr(user, 'secret_expires_at') else None,
            created_at=user.created_at,
            has_secret=bool(user.totp_secret),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/secret")
async def save_secret(request: SaveSecretRequest, db: Session = Depends(get_db)):
    try:
        await secrets_service.save_user_secret(db, request.username, request.secret_plain)
        # Обновим срок истечения секрета, если передан
        user = db.query(User).filter(User.username == request.username).first()
        if request.secret_expires_at:
            user.secret_expires_at = request.secret_expires_at
            db.commit()
        return {"message": "Секрет сохранен"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{username}/secret")
async def revoke_secret(username: str, db: Session = Depends(get_db)):
    try:
        await secrets_service.revoke_access(db, username)
        return {"message": "Доступ отозван (секрет удален)"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{username}")
async def delete_user(username: str, db: Session = Depends(get_db)):
    try:
        await secrets_service.delete_user(db, username)
        return {"message": "Пользователь удален"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/verify", response_model=TotpVerifyResponse)
async def verify_totp(request: TotpVerifyRequest, db: Session = Depends(get_db)):
    return await secrets_service.verify_totp(db, request)


@router.get("/users", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            secret_expires_at=user.secret_expires_at if hasattr(user, 'secret_expires_at') else None,
            created_at=user.created_at,
            has_secret=bool(user.totp_secret),
        )
        for user in users
    ]