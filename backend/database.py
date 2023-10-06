import sqlite3
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
                    (`id` INTEGER NOT NULL, `username` TEXT NOT NULL, `path` TEXT NOT NULL, PRIMARY KEY(`id` AUTOINCREMENT) );'''
        print(sql)
        cursor.execute(sql)
        print('ok')
    except Exception:
        print('Error create_history_table')

def add_history(username, path):
    cursor = conn.cursor()
    try:
        cursor.execute(f"""INSERT INTO `history_{datetime.now().strftime("%Y%m")}` (`username`, `path`)
                       VALUES ('{username}', '{path}')""")
    except Exception:
        print('Exception add_history')