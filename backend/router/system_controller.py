from fastapi import APIRouter, Depends, File
from model.user import User
from service.user_service import get_current_user
from service.system_service import create_user, get_system_config, update_system_config, get_user_statistic, verify_detection

system_router = APIRouter(tags=["system"])

@system_router.post('/create_user')
async def register(username: str, password: str, user: User = Depends(get_current_user)):
    return create_user(username, password, user)

@system_router.get('/get_config')
async def get_config():
    return get_system_config()

@system_router.post('/update_config')
async def update_config(file:str, roi:str, obj_size: str, user: User = Depends(get_current_user)):
    return update_system_config(file, roi, obj_size, user)

@system_router.post('/statistic')
async def get_statistic(user: User = Depends(get_current_user)):
    return get_user_statistic(user)

@system_router.post("/verify")
async def verify(bbox: str, file: bytes = File(...)):
    return verify_detection(bbox, file)