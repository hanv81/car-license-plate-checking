from mysql.connector import Error
from mysql.connector import pooling
from datetime import datetime
import traceback, logging

connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool", pool_size=5,
                                              pool_reset_session=True, host='localhost',
                                              database='car-door-plate', user='root', password='180981')
logging.basicConfig(filename='database.log', encoding='utf-8', level=logging.DEBUG)

def create_user(username, password, refresh_token):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    result = True
    try:
        cursor.execute(f"""INSERT INTO `user` (`username`, `password`, `refresh_token`)
                       VALUES ('{username}', '{password}', '{refresh_token}')""")
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'create_user {username} {password} {refresh_token}')
        result = False
    finally:
        cursor.close()
        conn.close()
    
    return result

def get_user(username):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM `user` WHERE `username`='{username}'")
        result = cursor.fetchone()
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'get_user {username}')
        return None
    finally:
        cursor.close()
        conn.close()
    return result

def get_user_plate(plate):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT `username` FROM `user_plate` WHERE `plate`='{plate}'")
        result = cursor.fetchone()
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'get_user_plate {plate}')
        return None
    finally:
        cursor.close()
        conn.close()
    return result

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

def get_user_plates(username):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT `plate` FROM `user_plate` WHERE `username`='{username}'")
        result = cursor.fetchall()
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'get_user_plates {username}')
        return None
    finally:
        cursor.close()
        conn.close()
    return result

def register_plate(username, plate):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    result = True
    try:
        cursor.execute(f"""INSERT INTO `user_plate` (`username`, `plate`) 
                       VALUES ('{username}', '{plate}')""")
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'register_plate {username} {plate}')
        result = False
    finally:
        cursor.close()
        conn.close()
    return result

def delete_plate(username, plate):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    result = True
    try:
        cursor.execute(f"""DELETE FROM `user_plate` WHERE `username`='{username}' AND `plate`='{plate}'""")
        conn.commit()
    except Error:
        traceback.print_exc()
        logging.exception(f'delete_plate {username} {plate}')
        result = False
    finally:
        cursor.close()
        conn.close()
    return result

def create_history_table():
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        sql = f'''CREATE TABLE IF NOT EXISTS `history_{datetime.now().strftime("%Y%m")}`
                (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
                `username` VARCHAR(20) NOT NULL COLLATE 'utf8mb4_general_ci',
                `plate` VARCHAR(20) NOT NULL COLLATE 'utf8mb4_general_ci',
                `region` VARCHAR(10) NOT NULL COLLATE 'utf8mb4_general_ci',
                `type` VARCHAR(10) NOT NULL COLLATE 'utf8mb4_general_ci',
                `bbox` VARCHAR(30) NOT NULL COLLATE 'utf8mb4_general_ci',
                `path` TEXT NOT NULL COLLATE 'utf8mb4_general_ci',
                PRIMARY KEY (`id`) USING BTREE)
                COLLATE='utf8mb4_general_ci'
                ENGINE=InnoDB;'''
        cursor.execute(sql)
        conn.commit()
    except Exception:
        traceback.print_exc()
        logging.exception('create_history_table')
    finally:
        cursor.close()
        conn.close()

def add_history(username, plate, region, type, bbox, path):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO `history_{datetime.now().strftime("%Y%m")}`
                       (`username`, `plate`, `region`, `type`, `bbox`, `path`)
                       VALUES ('{username}', '{plate}', '{region}', '{type}', '{bbox}', '{path}')""")
        conn.commit()
    except Exception:
        traceback.print_exc()
        logging.exception(f'add_history {username} {plate} {bbox} {path}')
    finally:
        cursor.close()
        conn.close()

def get_user_history(username):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT plate, bbox, path FROM `history_{datetime.now().strftime("%Y%m")}`
                       WHERE `username`='{username}'""")
        result = cursor.fetchall()
        conn.commit()
    except:
        traceback.print_exc()
        logging.exception(f'get_user_history {username}')
        result = None
    finally:
        cursor.close()
        conn.close()
    return result

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