import  mysql.connector
import sqlite3
from PySide6.QtSql import QSqlDatabase, QSqlQueryModel
import os
from datetime import datetime


db_file = 'chat.db'
init_username = 'admin'
init_password='123456'


def create_db():
    if not os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL,
                            password TEXT NOT NULL
                        )''')
        cursor.execute('''CREATE TABLE chat_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL,
                            modelname TEXT NOT NULL,
                            message TEXT NOT NULL,
                            voice_path TEXT NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')
        conn.commit()
        cursor.close()
        conn.close()
        init_user()

def init_user():
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=?', (init_username,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (init_username, init_password))
        conn.commit()
    cursor.close()
    conn.close()
    

def add_chat(username,modelname, message,voice_path,timestamp=datetime.now().strftime("%Y-%m-%d")):
    if voice_path=='' or voice_path==None:
        voice_path='None'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO chat_history (username,modelname,message,voice_path,timestamp) VALUES (?, ?,?,?,?)', (username,modelname, message,voice_path,timestamp))
    conn.commit()
    cursor.close()
    conn.close()