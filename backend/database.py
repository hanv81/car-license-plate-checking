import sqlite3
import traceback
from datetime import datetime

conn = sqlite3.connect('data.db')

def create_user(username, password, refresh_token):
    cursor = conn.cursor()
    try:
        result = cursor.execute(f"""INSERT INTO `user` (`username`, `password`, `refresh_token`) 
                                VALUES ('{username}', '{password}', '{refresh_token}')""")
        conn.commit()
    except Exception:
        result = None
    return result

def get_user(username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM `user` WHERE `username`='{username}'")
    conn.commit()
    return cursor.fetchone()

def get_user_plate(plate):
    cursor = conn.cursor()
    cursor.execute(f"SELECT `username` FROM `user_plate` WHERE `plate`='{plate}'")
    conn.commit()
    return cursor.fetchone()

def get_user_plates(username):
    cursor = conn.cursor()
    cursor.execute(f"SELECT `plate` FROM `user_plate` WHERE `username`='{username}'")
    conn.commit()
    return cursor.fetchall()

def delete_plate(username, plate):
    cursor = conn.cursor()
    try:
        result = cursor.execute(f"""DELETE FROM `user_plate` 
                                WHERE `username`='{username}' AND `plate`='{plate}'""")
        conn.commit()
    except Exception:
        result = None
    return result

def register_plate(username, plate):
    cursor = conn.cursor()
    try:
        result = cursor.execute(f"""INSERT INTO `user_plate` (`username`, `plate`) 
                                VALUES ('{username}', '{plate}')""")
        conn.commit()
    except Exception:
        result = None
    return result

def create_history_table():
    cursor = conn.cursor()
    try:
        sql = f'''CREATE TABLE `history_{datetime.now().strftime("%Y%m")}`
                    (`id` INTEGER NOT NULL,
                    `username` TEXT NOT NULL,
                    `plate` TEXT NOT NULL,
                    `path` TEXT NOT NULL,
                    PRIMARY KEY(`id` AUTOINCREMENT) );'''
        cursor.execute(sql)
        conn.commit()
    except Exception:
        print('Error create_history_table')
        traceback.print_exc()

def add_history(username, plate, path):
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO `history_{datetime.now().strftime("%Y%m")}` (`username`, `plate`, `path`)
                       VALUES ('{username}', '{plate}', '{path}')""")
        conn.commit()
    except Exception:
        print('Exception add_history')

def get_user_history(username):
    cursor = conn.cursor()
    try:
        cursor.execute(f"""SELECT plate, path FROM `history_{datetime.now().strftime("%Y%m")}`
                       WHERE `username`='{username}'""")
        conn.commit()
        result = cursor.fetchall()
    except:
        traceback.print_exc()
        result = None
    return result