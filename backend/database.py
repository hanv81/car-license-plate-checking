from mysql.connector import Error
from mysql.connector import pooling
from datetime import datetime
import traceback

connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool", pool_size=5,
                                              pool_reset_session=True, host='localhost',
                                              database='car-door-plate', user='root', password='180981')

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
        result = False
    finally:
        cursor.close()
        conn.close()
    return result

def create_history_table():
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        sql = f'''CREATE TABLE `history_{datetime.now().strftime("%Y%m")}`
                (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
                `username` VARCHAR(20) NOT NULL COLLATE 'utf8mb4_general_ci',
                `plate` VARCHAR(20) NOT NULL COLLATE 'utf8mb4_general_ci',
                `path` TEXT NOT NULL COLLATE 'utf8mb4_general_ci',
                PRIMARY KEY (`id`) USING BTREE)
                COLLATE='utf8mb4_general_ci'
                ENGINE=InnoDB;'''
        cursor.execute(sql)
        conn.commit()
    except Exception:
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

def add_history(username, plate, path):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO `history_{datetime.now().strftime("%Y%m")}` (`username`, `plate`, `path`)
                       VALUES ('{username}', '{plate}', '{path}')""")
        conn.commit()
    except Exception:
        print('Exception add_history')
    finally:
        cursor.close()
        conn.close()

def get_user_history(username):
    conn = connection_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT plate, path FROM `history_{datetime.now().strftime("%Y%m")}`
                       WHERE `username`='{username}'""")
        result = cursor.fetchall()
        conn.commit()
    except:
        traceback.print_exc()
        result = None
    finally:
        cursor.close()
        conn.close()
    return result