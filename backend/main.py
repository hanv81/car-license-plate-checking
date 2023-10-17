import requests, io, os, time, traceback
import database as db
import numpy as np
from datetime import datetime, timedelta
from typing import Union
from concurrent.futures import ThreadPoolExecutor
from fastapi import Depends, FastAPI, HTTPException, status, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from PIL import Image

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()
OCR_API_URL = 'https://api.platerecognizer.com/v1/plate-reader/'
OCR_HEADER = {'Authorization': 'Token 45f3172a25b6ea562e6174ac2475b7ca26b8e2fc'}
executor = ThreadPoolExecutor()

credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail="Could not validate credentials",
                                      headers={"WWW-Authenticate": "Bearer"},)
username_existed_exception = HTTPException(status_code=status.HTTP_201_CREATED,
                                      detail="Username exist",
                                      headers={"WWW-Authenticate": "Bearer"},)
internal_server_exception = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                      detail="Database error",
                                      headers={"WWW-Authenticate": "Bearer"},)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None

class User(BaseModel):
    id: int
    username: str
    password: str
    refresh_token: str

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(milliseconds=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.get_user(token_data.username)
    if user is None:
        raise credentials_exception

    return user

@app.get('/create_user')
async def create_user(username: str, password: str):
    data = {'username':username, 'password':password}
    refresh_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    if db.create_user(username, pwd_context.hash(password), refresh_token):
        return data
    raise username_existed_exception

@app.post("/login")
async def login(data: OAuth2PasswordRequestForm = Depends()):
    user = db.get_user(data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Username not exist",
                            headers={"WWW-Authenticate": "Bearer"})

    if not pwd_context.verify(data.password, user[2]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Wrong password",
                            headers={"WWW-Authenticate": "Bearer"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": data.username},
                                       expires_delta=access_token_expires)

    return {"refresh_token": user[3], "access_token": access_token, "token_type": "bearer"}

@app.post('/register_plate')
async def register_plate(plate: str, user: User = Depends(get_current_user)):
    if db.register_plate(user[1], plate):
        return user
    raise internal_server_exception

@app.post('/get_plates')
async def get_plates(user: User = Depends(get_current_user)):
    plates = db.get_user_plates(user[1])
    plates = [plates[i][0] for i in range(len(plates))]
    return plates

@app.post('/delete_plate')
async def delete_plate(plate: str, user: User = Depends(get_current_user)):
    result = db.delete_plate(user[1], plate)
    if result is None:
        raise internal_server_exception

def log_history(image, username, plate, bbox):
    folder = datetime.now().strftime("%Y%m")
    os.makedirs(os.path.join('history', folder), exist_ok=True)
    path = 'history/' + folder + '/' + username + str(time.time_ns()) + '.jpg'
    image.save(path)
    # db.create_history_table()
    db.add_history(username, plate, bbox, path)

@app.post("/verify")
async def verify(bbox: str, file: bytes = File(...)):
    try:
        x1,y1,x2,y2 = map(int, bbox.split())
        image = Image.open(io.BytesIO(file))
        frame = np.array(image)[y1:y2, x1:x2]
        byte_io = io.BytesIO()
        Image.fromarray(frame).save(byte_io, format='PNG')
        response = requests.post(url=OCR_API_URL, headers=OCR_HEADER, files=dict(upload=byte_io.getvalue()))
        results = response.json().get('results')
        identified = False
        msg = 'Unidentified'
        if results is not None and len(results) > 0:
            plate = results[0]['plate']
            msg = plate
            username = db.get_user_plate(plate)
            if username:
                username = username[0]
                msg = f'{plate} {username}'
                identified = True
                executor.submit(log_history, image, username, plate, bbox)
    except:
        traceback.print_exc()
        raise internal_server_exception

    return {'msg':msg, 'identified':identified}

@app.post('/get_history')
async def get_history(user: User = Depends(get_current_user)):
    history = db.get_user_history(user[1])
    if history is None:
        raise internal_server_exception
    
    return history

@app.get('/get_config')
async def get_config():
    db_config = db.get_config()
    config = {}
    for i in range(len(db_config)):
        key, value = db_config[i]
        db_config[i] = {key:value}
        config[key] = value
    return config

@app.post('/update_config')
async def update_config(file:str, roi:str):
    if not db.update_config('file', file):
        raise internal_server_exception
    if not db.update_config('roi', roi):
        raise internal_server_exception