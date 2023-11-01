from mysql.connector import Error
from mysql.connector import pooling
from datetime import datetime
import traceback, logging
from model.user import User, Plate
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import List

connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool", pool_size=5,
                                              pool_reset_session=True, host='localhost',
                                              database='car-door-plate', user='root', password='180981')
logging.basicConfig(filename='database.log', encoding='utf-8', level=logging.DEBUG)

def create_user(username, password, refresh_token, session: Session):
    session.add(User(username=username, password=password, refresh_token=refresh_token))
    session.commit()

def get_user(username, session: Session) -> User:
    return session.query(User).filter(User.username == username).one()

def get_user_plate(plate, session: Session) -> Plate:
    result = session.query(Plate).filter(Plate.plate == plate)
    return result.one() if result.count() > 0 else None

def get_user_by_plates(plates):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        str_plates = ','.join(plates)
        cursor.execute(f"SELECT `username`,`plate` FROM `user_plate` WHERE `plate` IN ({str_plates})")
        result = cursor.fetchone()
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'get_user_plates {plates}')
        return None
    finally:
        cursor.close()
        conn.close()
    return result

def get_user_plates(username, session: Session) -> List[Plate]:
    return session.query(Plate).filter(Plate.username == username).all()

def register_plate(username, plate, session: Session):
    session.add(Plate(username=username, plate=plate))
    session.commit()

def delete_plate(username, plate, session: Session):
    plate = session.query(Plate).filter(Plate.username == username, Plate.plate == plate).one()
    if plate is not None:
        session.delete(plate)

def create_history_table(session: Session):
    try:
        statement = text(f'''CREATE TABLE IF NOT EXISTS `history_{datetime.now().strftime("%Y%m")}`
                (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
                `username` VARCHAR(20) NOT NULL COLLATE 'utf8mb4_general_ci',
                `plate` VARCHAR(20) NOT NULL COLLATE 'utf8mb4_general_ci',
                `region` VARCHAR(10) NOT NULL COLLATE 'utf8mb4_general_ci',
                `type` VARCHAR(30) NOT NULL COLLATE 'utf8mb4_general_ci',
                `bbox` VARCHAR(30) NOT NULL COLLATE 'utf8mb4_general_ci',
                `path` TEXT NOT NULL COLLATE 'utf8mb4_general_ci',
                `create_time` TIMESTAMP NOT NULL DEFAULT (now()),
                PRIMARY KEY (`id`) USING BTREE)
                COLLATE='utf8mb4_general_ci'
                ENGINE=InnoDB;''')
        session.execute(statement)
        session.commit()
    except Exception:
        traceback.print_exc()
        logging.exception('create_history_table')

def add_history(username, plate, region, type, bbox, path, session: Session):
    try:
        statement = text(f"""INSERT INTO `history_{datetime.now().strftime("%Y%m")}`
                        (`username`, `plate`, `region`, `type`, `bbox`, `path`)
                        VALUES ('{username}', '{plate}', '{region}', '{type}', '{bbox}', '{path}')""")
        session.execute(statement)
        session.commit()
    except:
        traceback.print_exc()
        logging.exception(f'add_history {username} {plate} {region} {type} {bbox} {path}')

def get_user_history(username, session: Session):
    statement = text(f"""SELECT plate, bbox, path FROM `history_{datetime.now().strftime("%Y%m")}`
                       WHERE `username`='{username}'""")
    result = session.execute(statement)
    return result.all()

def get_config():
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT `name`,`value` FROM `config`""")
        result = cursor.fetchall()
        conn.commit()
    except:
        traceback.print_exc()
        logging.exception('get_config')
        result = None
    finally:
        cursor.close()
        conn.close()
    return result

def update_config(name, value):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    result = True
    try:
        cursor.execute(f"""UPDATE `config` SET `value`='{value}' WHERE `name`='{name}'""")
        conn.commit()
    except:
        traceback.print_exc()
        logging.exception('update_config')
        result = False
    finally:
        cursor.close()
        conn.close()
    return result

def get_list_user(session: Session):
    return session.query(User).filter(User.user_type == 0).all()

def get_list_car(session: Session):
    cars = session.query(Plate).join(User, User.username == Plate.username).all()
    return [(c.plate, c.username) for c in cars]

def get_daily_statistic(session: Session):
    statement = text(f"""SELECT `type`, DATE(`create_time`), COUNT(`type`)
                       FROM `history_{datetime.now().strftime("%Y%m")}` GROUP BY `type`, DATE(`create_time`)""")
    result = session.execute(statement)
    return [tuple(row) for row in result.all()]