from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from model.user import User
from util.session import create_session
from sqlalchemy.orm import Session
from service.user_service import get_current_user, authenticate, get_user_plates, register_user_plate, delete_user_plate, get_user_history

user_router = APIRouter(tags=["user"])

@user_router.post('/login')
async def login(data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(create_session)):
    return authenticate(data, session)

@user_router.post('/get_plates')
async def get_plates(user: User = Depends(get_current_user), session: Session = Depends(create_session)):
    return get_user_plates(user, session)

@user_router.post('/register_plate')
async def register_plate(plate: str, user: User = Depends(get_current_user), session: Session = Depends(create_session)):
    return register_user_plate(plate, user, session)

@user_router.post('/delete_plate')
async def delete_plate(plate: str, user: User = Depends(get_current_user), session: Session = Depends(create_session)):
    return delete_user_plate(plate, user, session)

@user_router.post('/get_history')
async def get_history(user: User = Depends(get_current_user), session: Session = Depends(create_session)):
    return get_user_history(user, session)