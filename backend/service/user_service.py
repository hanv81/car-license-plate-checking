from typing import Union
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from model.user import User
from sqlalchemy.orm import Session
from util.session import create_session
import service.database as db

ALGORITHM = "HS256"
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail="Could not validate credentials",
                                      headers={"WWW-Authenticate": "Bearer"},)
internal_server_exception = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                          detail="Database error",
                                          headers={"WWW-Authenticate": "Bearer"},)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(milliseconds=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(create_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.get_user(username, session)
    if user is None:
        raise credentials_exception

    return User(id=user.id, username=user.username, password=user.password, refresh_token=user.refresh_token, user_type=user.user_type)

def authenticate(data, session: Session):
    user = db.get_user(data.username, session)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Username not exist",
                            headers={"WWW-Authenticate": "Bearer"})

    if not pwd_context.verify(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Wrong password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": data.username},
                                       expires_delta=access_token_expires)

    return {"refresh_token": user.refresh_token, "access_token": access_token}

def get_user_plates(user: User):
    plates = db.get_user_plates(user.username)
    plates = [plates[i][0] for i in range(len(plates))]
    return plates

def register_user_plate(plate: str, user: User):
    if db.register_plate(user.username, plate):
        return user
    raise internal_server_exception

def delete_user_plate(plate: str, user: User):
    result = db.delete_plate(user.username, plate)
    if result is None:
        raise internal_server_exception

def get_user_history(user: User):
    history = db.get_user_history(user.username)
    if history is None:
        raise internal_server_exception
    return history