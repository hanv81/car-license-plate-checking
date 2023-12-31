import io, os, time, traceback, requests
import numpy as np
import service.database as db
from jose import jwt
from PIL import Image
from datetime import datetime
from model.user import User
from fastapi import HTTPException, status
from passlib.context import CryptContext
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

ALGORITHM = "HS256"
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
OCR_API_URL = 'https://api.platerecognizer.com/v1/plate-reader/'
OCR_HEADER = {'Authorization': 'Token 45f3172a25b6ea562e6174ac2475b7ca26b8e2fc'}
# OCR_HEADER = {'Authorization': 'Token 579df3fbc1fb5f65459d9ce5ef6c24e9e1943bf3'}

usertype_not_accept_exception = HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                                              detail="User type not acceptable",
                                              headers={"WWW-Authenticate": "Bearer"},)
username_existed_exception = HTTPException(status_code=status.HTTP_201_CREATED,
                                           detail="Username exist",
                                           headers={"WWW-Authenticate": "Bearer"},)
internal_server_exception = HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                          detail="Server error",
                                          headers={"WWW-Authenticate": "Bearer"},)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
executor = ThreadPoolExecutor()

def create_user(username: str, password: str, user: User, session: Session):
    if user.user_type != 0:
        raise usertype_not_accept_exception
    data = {'username':username, 'password':password}
    refresh_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    try:
        db.create_user(username, pwd_context.hash(password), refresh_token, session)
        return data
    except:
        raise username_existed_exception

def get_system_config(session: Session):
    config = {}
    configs = db.get_config(session)
    for cf in configs:
        config[cf.name] = cf.value
    return config

def update_system_config(file: str, roi: str, obj_size: str, user: User, session: Session):
    if user.user_type != 0:
        raise usertype_not_accept_exception
    db.update_config('file', file, session)
    db.update_config('roi', roi, session)
    db.update_config('obj_size', obj_size, session)

def get_system_statistic(user: User, session: Session):
    if user.user_type != 0:
        raise usertype_not_accept_exception

    users = db.get_list_user(session)
    cars = db.get_list_car(session)
    statistic = db.get_daily_statistic(session)
    return users, cars, statistic

def log_history(image, username, plate, region, type, bbox, session: Session):
    folder = datetime.now().strftime("%Y%m")
    os.makedirs(os.path.join('history', folder), exist_ok=True)
    path = 'history/' + folder + '/' + username + str(time.time_ns()) + '.jpg'
    image.save(path)
    db.create_history_table(session)
    db.add_history(username, plate, region, type, bbox, path, session)

def verify_detection(bbox: str, file: bytes, session: Session):
    try:
        x1,y1,x2,y2 = map(int, bbox.split())
        image = Image.open(io.BytesIO(file))
        frame = np.array(image)[y1:y2, x1:x2]
        byte_io = io.BytesIO()
        Image.fromarray(frame).save(byte_io, format='PNG')
        response = requests.post(url=OCR_API_URL, headers=OCR_HEADER, files=dict(upload=byte_io.getvalue()))
        msg, identified = process_ocr_response(response, image, bbox, session)
    except:
        traceback.print_exc()
        raise internal_server_exception

    return {'msg':msg, 'identified':identified}

def process_ocr_response(response, image, bbox, session):
    identified = False
    if response.status_code != status.HTTP_201_CREATED:
        return response.json()['detail'], identified

    results = response.json()['results']
    if results is None or len(results) == 0:
        return 'Unidentified', identified

    plate = results[0]['plate']
    region = results[0]['region']['code']
    type = results[0]['vehicle']['type']
    msg = f'{plate} {region} {type}'
    p = db.get_user_plate(plate, session)
    if p:
        username = p.username
        msg += f' {username}'
        identified = True
        executor.submit(log_history, image, username, plate, region, type, bbox, session)

    return msg, identified