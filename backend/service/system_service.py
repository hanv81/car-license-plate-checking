import io, os, time, traceback, requests
import numpy as np
import database as db
from jose import jwt
from PIL import Image
from datetime import datetime
from model.user import User
from fastapi import HTTPException, status
from passlib.context import CryptContext
from concurrent.futures import ThreadPoolExecutor

ALGORITHM = "HS256"
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
OCR_API_URL = 'https://api.platerecognizer.com/v1/plate-reader/'
OCR_HEADER = {'Authorization': 'Token 45f3172a25b6ea562e6174ac2475b7ca26b8e2fc'}

usertype_not_accept_exception = HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                              detail="User type not acceptable",
                                              headers={"WWW-Authenticate": "Bearer"},)
username_existed_exception = HTTPException(status_code=status.HTTP_201_CREATED,
                                           detail="Username exist",
                                           headers={"WWW-Authenticate": "Bearer"},)
internal_server_exception = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                          detail="Database error",
                                          headers={"WWW-Authenticate": "Bearer"},)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
executor = ThreadPoolExecutor()

def create_user(username: str, password: str, user: User):
    if user.user_type != 0:
        raise usertype_not_accept_exception
    data = {'username':username, 'password':password}
    refresh_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    if db.create_user(username, pwd_context.hash(password), refresh_token):
        return data
    raise username_existed_exception

def get_system_config():
    db_config = db.get_config()
    config = {}
    for i in range(len(db_config)):
        key, value = db_config[i]
        db_config[i] = {key:value}
        config[key] = value
    return config

def update_system_config(file: str, roi: str, obj_size: str, user: User):
    if user.user_type != 0:
        raise usertype_not_accept_exception
    if not db.update_config('file', file):
        raise internal_server_exception
    if not db.update_config('roi', roi):
        raise internal_server_exception
    if not db.update_config('obj_size', obj_size):
        raise internal_server_exception

def get_user_statistic(user: User):
    if user.user_type != 0:
        raise usertype_not_accept_exception

    users = db.get_list_user()
    cars = db.get_list_car()
    statistic = db.get_daily_statistic()
    return users, cars, statistic

def log_history(image, username, plate, region, type, bbox):
    folder = datetime.now().strftime("%Y%m")
    os.makedirs(os.path.join('history', folder), exist_ok=True)
    path = 'history/' + folder + '/' + username + str(time.time_ns()) + '.jpg'
    image.save(path)
    # db.create_history_table()
    db.add_history(username, plate, region, type, bbox, path)

def verify_detection(bbox: str, file: bytes):
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
            region = results[0]['region']['code']
            type = results[0]['vehicle']['type']
            msg = f'{plate} {region} {type}'
            username = db.get_user_plate(plate)
            if username:
                username = username[0]
                msg += f' {username}'
                identified = True
                executor.submit(log_history, image, username, plate, region, type, bbox)
    except:
        traceback.print_exc()
        raise internal_server_exception

    return {'msg':msg, 'identified':identified}